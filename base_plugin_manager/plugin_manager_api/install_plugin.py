from plugins.base_api_wrapper.tools import internal_ip_required
from flask import request
import tempfile
import git
import shutil
import os
import pa
import sys
from pa.bin.download_source import pa_root, get_all_depend_manifest, download_plugin
import zipfile


@internal_ip_required()
def install_plugin():
    git_url = request.form.get('git_url')
    branch = request.form.get('branch')
    path = request.form.get('path')
    zip_file = request.files['files'] if 'files' in request.files else None

    if git_url is not None and len(git_url) > 0:
        if branch is None or len(branch) == 0:
            branch = 'master'
        if len(path) > 0:
            if path[0] == '/':
                path = path[1:]
        with tempfile.TemporaryDirectory() as temp_path:
            try:
                git.Repo.clone_from(url=git_url, to_path=temp_path, branch=branch)
                _install_plugin(os.path.join(temp_path, path), temp_path)
            except Exception as e:
                pa.log.error('install plugin error: {0}'.format(e))
                return 'install plugin error: {0}'.format(e), 400
    elif zip_file is not None:
        with tempfile.TemporaryDirectory() as temp_path:
            plugin_paths = _unzip_to_path(zip_file, temp_path)
            try:
                for path in plugin_paths:
                    _install_plugin(path, temp_path)
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


def _install_plugin(plugin_path, temp_path):
    # 打开 manifest 文件
    manifest_file = os.path.join(plugin_path, '__manifest__.py')
    if not os.path.exists(manifest_file):
        raise FileNotFoundError('__manifest__.py not exists')

    # 获取所有该插件所依赖的其它插件
    try:
        depend_plugins = get_all_depend_manifest(pa_root, [manifest_file])
    except Exception as e:
        raise SyntaxError('unable load manifest file {0}'.format(e))

    # 下载并加载所有插件
    all_depend_plugin = {}
    for depend_name, depend_manifest in depend_plugins.items():
        # 查看插件是否已经安装并且版本匹配
        installed_plugin = None
        for plugin in pa.plugin_manager.all_installed_plugins:
            if plugin.manifest['name'] == depend_name:
                installed_plugin = plugin

        if installed_plugin is not None:
            if installed_plugin.manifest['version'] != depend_manifest['version']:
                raise ModuleNotFoundError('plugin \'{0}\' already installed, '
                                          'but version is not match (need: {1} found: {2})'
                                          .format(depend_manifest['name'],
                                                  depend_manifest['version'],
                                                  installed_plugin.manifest['version']))
            continue

        # 将插件下载到临时文件夹
        depend_temp_path = os.path.join(temp_path, depend_name)
        all_depend_plugin[depend_name] = depend_temp_path
        if not os.path.exists(depend_temp_path):
            with tempfile.TemporaryDirectory() as temp_path_2:
                download_plugin(pa_root, depend_name, temp_path_2, temp_path)
                shutil.copytree(os.path.join(temp_path, 'plugins', depend_name), depend_temp_path)
                shutil.rmtree(os.path.join(temp_path, 'plugins'))

        # 尝试从临时文件夹中加载插件，加载失败则会抛出异常导致安装失败
        pa.plugin_manager.load_extra_plugin(depend_temp_path)

    # 插件下载并预加载完毕，将插件拷贝到插件文件夹中
    pa_plugin_path = os.path.dirname(sys.modules['plugins'].__file__)
    for depend_name, depend_path in all_depend_plugin.items():
        dest_depend_path = os.path.join(pa_plugin_path, depend_name)
        if os.path.exists(dest_depend_path):
            shutil.rmtree(dest_depend_path)
        shutil.copytree(depend_path, dest_depend_path)
