from plugins.base_api_wrapper.tools import internal_ip_required
from plugins.base.models import Plugins
from flask import jsonify
import pa


@internal_ip_required()
def query_plugin():
    try:
        all_plugins = Plugins.query.all()
    except Exception as e:
        pa.log.error('query plugin error: {0}'.format(e))
        return 'query plugin error', 500

    all_plugin_desc = []
    for plugin in all_plugins:
        all_plugin_desc.append({
            'name': plugin.name,
            'version': plugin.version,
            'installed': plugin.installed,
            'install_time': plugin.install_datetime.strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify(all_plugin_desc), 200
