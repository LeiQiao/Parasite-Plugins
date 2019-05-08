import os
import pa
from pa.plugin import Plugin
import importlib
import ast
import sys
import errno


class PluginManager:
    all_installed_plugins = []

    def start(self, base_plugin, base_plugin_path):
        base_plugin.manifest = self._load_plugin_manifest(base_plugin_path)
        self.all_installed_plugins.append(base_plugin)
        self.load_plugins()

    def load_extra_plugin(self, extra_plugin_path):
        manifest = self._load_plugin_manifest(extra_plugin_path)
        self._load_plugin(manifest['name'], plugin_path=extra_plugin_path)

    def load_plugins(self):
        # 遍历插件文件夹获取所有所有插件
        plugin_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        plugins_need_load = []
        for root, dirs, files in os.walk(plugin_path):
            if plugin_path != root:
                continue
            for plugin_name in dirs:
                # trim '__pacache__' etc.
                if plugin_name.startswith('__'):
                    continue
                plugins_need_load.append(plugin_name)

        load_sequence = []
        if 'plugins' in pa.plugin_config['base']:
            load_sequence = pa.plugin_config['base']['plugins'].split(',')
        for plugin_name in reversed(load_sequence):
            plugin_name = plugin_name.strip()
            if len(plugin_name) == 0:
                continue

            if plugin_name in plugins_need_load:
                plugins_need_load.pop(plugins_need_load.index(plugin_name))
                plugins_need_load.insert(0, plugin_name)
            else:
                pa.log.warning('unable found plugin \'\' which is ordered in config file'.format(plugin_name))

        for plugin_name in plugins_need_load:
            self._load_plugin(plugin_name)

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

    def _load_plugin(self, plugin_name, plugin_version=None, plugin_path=None, depend_by=None):
        if len(plugin_name) == 0:
            return

        installed_plugin = self.get_plugin(plugin_name)
        if installed_plugin is not None:
            if plugin_version is not None and installed_plugin.manifest['version'] != plugin_version:
                raise ModuleNotFoundError('plugin \'{0}\' version is not match (need: {1} found: {2})'
                                          .format(plugin_name,
                                                  plugin_version,
                                                  installed_plugin.manifest['version']))
            return

        if plugin_path is None:
            plugin_path = 'plugins'
            plugin_module = '{0}.{1}'.format(plugin_path, plugin_name)
            clone_plugin_module = plugin_name
        else:
            plugin_module = os.path.basename(plugin_path)
            clone_plugin_module = 'plugins.{0}'.format(plugin_name)
            sys.path.insert(0, os.path.realpath(os.path.join(plugin_path, '..')))
        plugin = importlib.import_module(plugin_module)
        sys.modules[clone_plugin_module] = sys.modules[plugin_module]
        if not os.path.exists(os.path.join(plugin_path, '__init__.py')):
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    os.path.join(plugin_path, '__init__.py'))
        manifest = self._load_plugin_manifest(os.path.dirname(plugin.__file__))
        if manifest is None:
            raise ModuleNotFoundError('plugin \'{0} ({1})\' was not found \'__manifest__.py\' file'
                                      .format(plugin_name,
                                              'any' if plugin_version is None else plugin_version))

        if plugin_version is not None and plugin_version.lower() != manifest['version'].lower():
            raise ModuleNotFoundError('plugin \'{0}\' version is not match (need: {1} found: {2})'
                                      .format(plugin_name,
                                              plugin_version,
                                              manifest['version']))

        # 加载模块的依赖模块
        for depend_name in manifest['depends']:
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
            self._load_plugin(depend_name, depend_version, None, new_depend_by)

        # 获取模块的入口对象
        plugin_class = None
        for attribute_name in dir(plugin):
            if attribute_name.startswith('__'):
                continue
            attribute_value = getattr(plugin, attribute_name)
            if isinstance(attribute_value, type) and issubclass(attribute_value, Plugin):
                plugin_class = attribute_value
        if plugin_class is None:
            raise ModuleNotFoundError('plugin \'{0} ({1})\' has not found enterance'
                                      .format(manifest['name'],
                                              'any' if plugin_version is None else plugin_version))

        plugin = plugin_class(plugin_name=plugin_name, manifest=manifest)

        # 添加到已加载的插件列表
        self.all_installed_plugins.append(plugin)

        # 加载模块
        plugin.on_before_load()
        plugin.on_load()
        plugin.on_after_load()
