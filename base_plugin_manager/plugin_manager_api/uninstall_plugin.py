from plugins.base_api_wrapper.tools import internal_ip_required
from flask import request
import sys
import pa
import shutil


@internal_ip_required()
def uninstall_plugin():
    plugin_name = request.args.get('plugin_name')

    if plugin_name is None or len(plugin_name) == 0:
        return 'plugin_name is empty', 400

    # 获取要删除的插件
    delete_plugin = None
    for plugin in pa.plugin_manager.all_installed_plugins:
        if plugin.manifest['name'] == plugin_name:
            delete_plugin = plugin
        for depend in plugin.manifest['depends']:
            depend_name = depend.split(':')[0]
            if depend_name == plugin_name:
                pa.log.error('plugin \'{0}\' depend this plugin \'{0}\''
                             .format(plugin.manifest['name'], plugin_name))
                return 'uninstall plugin error: plugin \'{0}\' ' \
                       'depend on this plugin'.format(plugin.manifest['name']), 400

    # 插件不存在
    if delete_plugin is None:
        return 'plugin not exists', 400

    plugin_path = delete_plugin.plugin_path

    # 卸载插件，但插件在其它模块里注册的信息不会被卸载
    del sys.modules[delete_plugin.__module__]
    if plugin_path in sys.path:
        sys.path.pop(sys.path.index(plugin_path))
    index = pa.plugin_manager.all_installed_plugins.index(delete_plugin)
    pa.plugin_manager.all_installed_plugins.pop(index)

    # 删除插件文件夹
    shutil.rmtree(plugin_path)

    return 'Uninstall success, Please restart Parasite to take effect', 200
