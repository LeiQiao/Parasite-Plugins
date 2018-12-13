from plugins.base_api_wrapper.tools import internal_ip_required
from flask import jsonify
import pa


@internal_ip_required()
def query_plugin():
    all_plugin_desc = []
    for plugin in pa.plugin_manager.all_installed_plugins:
        all_plugin_desc.append({
            'name': plugin.manifest['name'],
            'version': plugin.manifest['version']
        })

    return jsonify(all_plugin_desc), 200
