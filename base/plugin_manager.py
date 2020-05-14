import os
import pa
from pa.plugin import Plugin
import importlib
import ast
import sys
import errno


class PluginManager:
    all_installed_plugins = []
    all_plugin_desc = []

    def start(self, base_plugin, base_plugin_path, extra_plugin_paths):
        base_plugin.manifest = self._load_plugin_manifest(base_plugin_path)
        self.all_installed_plugins.append(base_plugin)
        self.load_plugins(base_plugin_path, extra_plugin_paths)

    def load_plugins(self, base_plugin_path, extra_plugin_paths):
        plugin_path = os.path.realpath(os.path.join(base_plugin_path, '..'))

        # 遍历插件文件夹获取所有插件
        for root, dirs, files in os.walk(plugin_path):
            if plugin_path != root:
                continue
            for plugin_name in dirs:
                # trim '__pacache__', '.DB_Store' etc.
                if plugin_name.startswith('__') or plugin_name.startswith('.'):
                    continue
                PluginManager.all_plugin_desc.append({
                    'plugin_name': plugin_name,
                    'manifest': PluginManager._load_plugin_manifest(os.path.join(plugin_path, plugin_name)),
                    'plugin_path': None
                })

        # 遍历扩展文件夹获取所有外部插件
        for extra_plugin_path in extra_plugin_paths:
            extra_plugin_path = extra_plugin_path.strip()
            manifest = self._load_plugin_manifest(extra_plugin_path)

            exist_plugin = PluginManager.get_plugin_desc(manifest['name'])
            if exist_plugin is not None and extra_plugin_path != exist_plugin['plugin_path']:
                raise FileExistsError('duplicate plugin named \'{0}\''.format(manifest['name']))

            PluginManager.all_plugin_desc.append({
                'plugin_name': manifest['name'],
                'manifest': manifest,
                'plugin_path': extra_plugin_path
            })

        # 插件的加载顺序
        load_sequence = []
        if 'plugins' in pa.plugin_config['base']:
            load_sequence = pa.plugin_config['base']['plugins'].split(',')

        for plugin_name in load_sequence:
            plugins = PluginManager.get_all_depend_plugins(plugin_name)
            for plugin in plugins:
                self._load_plugin(plugin['plugin_name'], plugin['manifest'], plugin['plugin_path'])

    @staticmethod
    def get_all_depend_plugins(plugin_name, plugin_version=None, depend_by=None):
        sep_pos = plugin_name.find(':')
        if sep_pos >= 0:
            plugin_version = plugin_name[sep_pos+1:].strip()
            plugin_name = plugin_name[:sep_pos].strip()
        plugin = PluginManager.get_plugin_desc(plugin_name)
        if plugin_version is not None and plugin_version != plugin['manifest']['version']:
            raise ModuleNotFoundError('plugin \'{0}\' version is not match (need: {1} found: {2})'
                                      .format(plugin_name,
                                              plugin_version,
                                              plugin['manifest']['version']))

        depend_plugins = []

        # 加载模块的依赖模块
        for depend_name in plugin['manifest']['depends']:
            sep_pos = depend_name.find(':')
            if sep_pos >= 0:
                depend_version = depend_name[sep_pos+1:].strip()
                depend_name = depend_name[:sep_pos].strip()
            else:
                depend_version = None
                depend_name = depend_name.strip()

            if depend_by is None:
                depend_by = []
            else:
                # 循环依赖
                if plugin_name in depend_by:
                    raise RecursionError('recursive dependency: {0} -> {1}({2})'
                                         .format(' -> '.join(depend_by),
                                                 plugin_name,
                                                 'any' if plugin_version is None else plugin_version))
            new_depend_by = depend_by[:]
            new_depend_by.append(plugin_name)
            depend_depend_plugins = PluginManager.get_all_depend_plugins(depend_name, depend_version, new_depend_by)
            for depend_depend_plugin in depend_depend_plugins:
                if depend_depend_plugin in depend_plugins:
                    continue
                depend_plugins.append(depend_depend_plugin)
        depend_plugins.append(plugin)
        return depend_plugins



    @staticmethod
    def get_plugin_desc(plugin_name):
        for plugin_desc in PluginManager.all_plugin_desc:
            if plugin_desc['plugin_name'] == plugin_name:
                return plugin_desc
        return None

    @staticmethod
    def get_plugin(plugin_name):
        for installed_plugin in PluginManager.all_installed_plugins:
            if installed_plugin.manifest['name'] == plugin_name:
                return installed_plugin
        return None

    @staticmethod
    def _load_plugin_manifest(plugin_path):
        # 读取模块和描述信息
        try:
            with open(os.path.join(plugin_path, '__manifest__.py')) as f:
                manifest = ast.literal_eval(f.read())
                return manifest
        except Exception as e:
            str(e)
            pa.log.warning('loading plugin: \'{0}\' is not a plugin or missing __manifest__.py file, skip'
                           .format(os.path.basename(plugin_path)))
            return None

    def _load_plugin(self, plugin_name, manifest, plugin_path=None):
        if len(plugin_name) == 0:
            return

        installed_plugin = self.get_plugin(plugin_name)
        if installed_plugin is not None:
            return None

        if plugin_path is None:
            plugin_path = 'plugins'
            plugin_module = '{0}.{1}'.format(plugin_path, plugin_name)
            plugin_path = os.path.join(plugin_path, plugin_name)
            clone_plugin_module = plugin_name
        else:
            plugin_module = os.path.basename(plugin_path)
            clone_plugin_module = 'plugins.{0}'.format(plugin_name)
            sys.path.insert(0, os.path.realpath(os.path.join(plugin_path, '..')))

        if not os.path.exists(os.path.join(plugin_path, '__init__.py')):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    os.path.join(plugin_path, '__init__.py'))
        if manifest is None:
            raise ModuleNotFoundError('plugin \'{0}\' do NOT have \'__manifest__.py\' file'
                                      .format(plugin_name))

        # 加载模块
        plugin = importlib.import_module(plugin_module)
        sys.modules[clone_plugin_module] = sys.modules[plugin_module]

        keys = list(sys.modules.keys())
        for key in keys:
            if key.startswith(plugin_module + '.'):
                clone_key = clone_plugin_module + key[len(plugin_module):]
                sys.modules[clone_key] = sys.modules[key]

        # 获取模块的入口对象
        plugin_class = None
        for attribute_name in dir(plugin):
            if attribute_name.startswith('__'):
                continue
            attribute_value = getattr(plugin, attribute_name)
            if isinstance(attribute_value, type) and \
               issubclass(attribute_value, Plugin) and \
               getattr(attribute_value, '__pluginname__') == manifest['name']:
                plugin_class = attribute_value
        if plugin_class is None:
            raise ModuleNotFoundError('plugin \'{0} ({1})\' has not found enterance'
                                      .format(manifest['name'], manifest['version']))

        plugin = plugin_class(plugin_name=plugin_name, manifest=manifest, plugin_path=plugin_path)

        # 添加到已加载的插件列表
        self.all_installed_plugins.append(plugin)

        # 加载模块
        plugin.on_before_load()
        plugin.on_load()
        plugin.on_after_load()

        return plugin
