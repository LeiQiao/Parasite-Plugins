from plugins.base_api_wrapper.tools import internal_ip_required
from flask import request
import tempfile
import shutil
import os
import pa
import sys
import ast
import zipfile


@internal_ip_required()
def install_plugin():
    git_url = request.form.get('git_url')
    branch = request.form.get('branch')
    path = request.form.get('path')
    zip_file = request.files['files'] if 'files' in request.files else None
    force_replacement = request.form.get('force_replace', '')

    if git_url is not None and len(git_url) > 0:
        if branch is None or len(branch) == 0:
            branch = 'master'
        if path is None:
            return 'path is empty', 400
        if len(path) > 0:
            if path[0] == '/':
                path = path[1:]
        with tempfile.TemporaryDirectory() as temp_path:
            try:
                import git
                git.Repo.clone_from(url=git_url, to_path=temp_path, branch=branch)
                if force_replacement == '1':
                    replace_dir([os.path.join(temp_path, path)])
                else:
                    _install_plugins([os.path.join(temp_path, path)])
            except Exception as e:
                pa.log.error('install plugin error: {0}'.format(e))
                return 'install plugin error: {0}'.format(e), 400
    elif zip_file is not None:
        with tempfile.TemporaryDirectory() as temp_path:
            plugin_paths = _unzip_to_path(zip_file, temp_path)
            try:
                if force_replacement == '1':
                    replace_dir(plugin_paths)
                else:
                    _install_plugins(plugin_paths)
            except Exception as e:
                pa.log.error('install plugin error: {0}'.format(e))
                return 'install plugin error: {0}'.format(e), 400
    else:
        return 'url or file is empty', 400

    return 'Install success, Please restart Parasite to take effect', 200


# 解压文件到文件夹
def _unzip_to_path(zip_file, temp_path):
    zip_path = os.path.join(temp_path, zip_file.filename)
    zip_file.save(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            filename = file.encode('cp437').decode('gbk')
            zip_ref.extract(file, temp_path)
            os.rename(os.path.join(temp_path, file), os.path.join(temp_path, filename))

    plugin_paths = []
    for root, dirs, files in os.walk(temp_path):
        if temp_path != root:
            continue
        for plugin_name in dirs:
            # trim '__pacache__' etc.
            if plugin_name.startswith('__'):
                continue
            plugin_paths.append(os.path.join(temp_path, plugin_name))
    return plugin_paths


def replace_dir(plugin_paths):
    pa_plugin_path = os.path.dirname(sys.modules['plugins'].__file__)
    pa.log.info(pa_plugin_path)
    for plugin_path in plugin_paths:
        # 设置插件的路径
        plugin_path_name = os.path.basename(plugin_path)
        dest_depend_path = os.path.join(pa_plugin_path, plugin_path_name)
        shutil.rmtree(dest_depend_path)
        shutil.copytree(plugin_path, dest_depend_path)


def _install_plugins(plugin_paths):
    all_manifest = []
    for plugin_path in plugin_paths:
        manifest_file = os.path.join(plugin_path, '__manifest__.py')
        if not os.path.exists(manifest_file):
            raise FileNotFoundError('__manifest__.py not exists')
        try:
            with open(manifest_file) as f:
                manifest = ast.literal_eval(f.read())
                manifest['plugin_path'] = plugin_path
        except Exception as e:
            raise SyntaxError('unable load manifest file {0}'.format(e))

        all_manifest.append(manifest)

    # 安装顺序
    install_order = []

    for manifest in all_manifest:
        # 查看插件是否已经安装
        already_exist = False
        for plugin in pa.plugin_manager.all_installed_plugins:
            # 版本是否一致
            if plugin.manifest['name'] == manifest['name'] and plugin.manifest['version'] == manifest['version']:
                already_exist = True
                break
        if already_exist:
            continue

        for depend in manifest['depends']:
            name_and_version = depend.split(':')
            depend_name = name_and_version[0].strip()
            if len(name_and_version) > 1:
                depend_version = name_and_version[1].strip()
            else:
                depend_version = None

            # 查看插件依赖项是否已经安装
            installed_plugin = None
            for plugin in pa.plugin_manager.all_installed_plugins:
                # 版本是否一致
                if plugin.manifest['name'] == depend_name:
                    if depend_version is not None and installed_plugin.manifest['version'] != depend_version:
                        raise ModuleNotFoundError('plugin \'{0}\' already installed, '
                                                  'but version is not match (need: {1} found: {2})'
                                                  .format(depend_name,
                                                          depend_version,
                                                          installed_plugin.manifest['version']))
                    installed_plugin = plugin
                    break

            # 插件已经安装，跳过
            if installed_plugin is not None:
                continue

            # 安装包中是否存在依赖的插件
            depend_manifest = None
            for m in all_manifest:
                if m['name'] == depend_name and (depend_version is None or m['version'] == depend_version):
                    depend_manifest = m
                    break

            if depend_manifest is None:
                raise ModuleNotFoundError('depend plugin \'{0}\' not found'.format(depend))

            # 将依赖包添加到待安装列表中
            if depend_manifest not in install_order:
                # 如果当前插件已经被前面的插件依赖，则该插件的依赖包放到该插件在待安装列表中的前面
                if manifest in install_order:
                    index = install_order.index(manifest)
                    install_order.insert(index, depend_manifest)
                else:
                    install_order.append(depend_manifest)
            else:
                # 如果依赖包和当前插件都在待安装列表中，将当前插件的安装顺序放在依赖包后面
                if manifest in install_order:
                    install_order.pop(install_order.index(manifest))
                    insert_index = install_order.index(depend_manifest)
                    install_order.insert(insert_index+1, manifest)

        # 如果当前插件没有被其他待安装插件依赖，则添加到待安装插件的最尾端
        if manifest not in install_order:
            install_order.append(manifest)

    # 安装插件
    pa_plugin_path = os.path.dirname(sys.modules['plugins'].__file__)
    for manifest in install_order:
        installed_plugin = None
        for plugin in pa.plugin_manager.all_installed_plugins:
            # 版本是否一致
            if plugin.manifest['name'] == manifest['name']:
                # 由于某些插件的资源无法卸载，所以旧插件需要先删除
                if plugin.manifest['version'] != manifest['version']:
                    raise FileExistsError('old plugin version \'{0}:{1}\' must uninstall first'
                                          .format(plugin.manifest['name'], plugin.manifest['version']))
                    # manifest['old_plugin_path'] = os.path.dirname(sys.modules[plugin.__module__].__file__)
                    # # 版本不一致卸载老版本插件
                    # del sys.modules[plugin.__module__]
                    # index = pa.plugin_manager.all_installed_plugins.index(plugin)
                    # pa.plugin_manager.all_installed_plugins.pop(index)
                    # break
                else:
                    installed_plugin = plugin
                    break

        if installed_plugin is not None:
            continue

        # 尝试从临时文件夹中加载插件，加载失败则会抛出异常导致安装失败
        plugin = pa.plugin_manager.load_extra_plugin(manifest['plugin_path'])

        # 设置插件的路径
        plugin_path_name = os.path.basename(manifest['plugin_path'])
        dest_depend_path = os.path.join(pa_plugin_path, plugin_path_name)
        plugin.plugin_path = dest_depend_path

    # 插件全部加载完毕，将插件拷贝至插件目录
    for manifest in install_order:
        # if 'old_plugin_path' in manifest and os.path.exists(manifest['old_plugin_path']):
        #     shutil.rmtree(manifest['old_plugin_path'])
        installed_plugin = None
        for plugin in pa.plugin_manager.all_installed_plugins:
            if plugin.manifest['name'] == manifest['name'] and plugin.manifest['version'] == manifest['version']:
                installed_plugin = plugin
                break

        if not installed_plugin:
            raise ModuleNotFoundError('plugin \'{0}:{1}\' not found'.format(manifest['name'], manifest['version']))

        if os.path.exists(installed_plugin.plugin_path):
            raise FileExistsError('path already exists \'{0}\''.format(installed_plugin.plugin_path))
        shutil.copytree(manifest['plugin_path'], installed_plugin.plugin_path)
