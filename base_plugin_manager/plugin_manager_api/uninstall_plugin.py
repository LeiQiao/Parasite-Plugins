from plugins.base_api_wrapper.tools import internal_ip_required
from flask import request
import sys
import os
from plugins.base.models import Plugins
import pa
import ast
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

    try:
        installed_plugins = Plugins.query.filter_by(installed=1).all()
    except Exception as e:
        pa.log.error('unable query table \'Plugin\': {0}'.format(e))
        return 'uninstall plugin error: {0}'.format(e), 500

    plugin_db_record = None

    # 遍历所有插件是否有依赖该插件
    for plugin in installed_plugins:
        if plugin.name == plugin_name:
            plugin_db_record = plugin
            continue
        plugin_path = os.path.join(pa_plugin_path, plugin.name)
        plugin_manifest_file = os.path.join(plugin_path, '__manifest__.py')
        with open(plugin_manifest_file) as f:
            manifest = ast.literal_eval(f.read())
        for depend in manifest['depends']:
            depend_name = depend.split(':')[0]
            if depend_name == plugin_name:
                pa.log.error('plugin \'{0}\' depend this plugin \'{0}\''
                             .format(manifest['name'], plugin_name))
                return 'uninstall plugin error: plugin \'{0}\' ' \
                       'depend on this plugin'.format(manifest['name']), 400

    # 删除已安装插件的数据库记录
    if plugin_db_record is not None:
        try:
            pa.database.session.delete(plugin_db_record)
            pa.database.session.commit()
        except Exception as e:
            pa.log.error('unable delete record from table \'Plugins\' {0}'.format(e))
            return 'uninstall plugin error: unable delete from database', 500

    # 删除插件文件夹
    plugin_path = os.path.join(pa_plugin_path, plugin_name)
    shutil.rmtree(plugin_path)

    # todo: 强制删除插件的数据库表

    return 'Uninstall success, Please restart Parasite to take effect', 200
