from plugins.base_api_wrapper.tools import internal_ip_required
from flask import request
import sys
import os
import pa
import shutil


@internal_ip_required()
def uninstall_plugin():
    plugin_name = request.args.get('plugin_name')

    if plugin_name is None or len(plugin_name) == 0:
        return 'plugin_name is empty', 400

    # 插件文件夹是否存在
    pa_plugin_path = os.path.dirname(sys.modules['plugins'].__file__)
    if not os.path.exists(os.path.join(pa_plugin_path, plugin_name)):
        return 'plugin not exists', 400

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

    # 删除插件文件夹
    plugin_path = os.path.join(pa_plugin_path, plugin_name)
    shutil.rmtree(plugin_path)
    if delete_plugin is not None:
        index = pa.plugin_manager.all_installed_plugins.index(delete_plugin)
        pa.plugin_manager.all_installed_plugins.pop(index)

    # todo: 强制删除插件的数据库表

    return 'Uninstall success, Please restart Parasite to take effect', 200
