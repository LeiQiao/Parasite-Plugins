import pa
from .config_model import ConfigModelRegister
from flask import jsonify, request
from plugins.base_api_warpper import internal_ip_required


@internal_ip_required()
def get_plugin_config():
    try:
        plugin_name = request.args.get('plugin_name')
    except Exception as e:
        pa.log.error(e)
        plugin_name = None

    if plugin_name is None:
        return '\'plugin_name\' is empty', 400

    plugin_config = None
    for config_class in ConfigModelRegister.all_plugin_config:
        if config_class.__plugin_name__ == plugin_name:
            plugin_config = config_class()
            break

    if plugin_config is None:
        return 'plugin \'{0}\' not exists'.format(plugin_name), 404

    config_json = plugin_config.dump_to_json()
    return jsonify(config_json), 200


@internal_ip_required()
def set_plugin_config():
    if 'plugin_name' not in request.json:
        return 'plugin_name is empty', 400
    plugin_name = request.json['plugin_name']

    if 'config' not in request.json:
        return 'config is empty', 400
    config_json = request.json['config']

    plugin_config = None
    for config_class in ConfigModelRegister.all_plugin_config:
        if config_class.__plugin_name__ == plugin_name:
            plugin_config = config_class()
            break

    if plugin_config is None:
        return 'plugin \'{0}\' not exists'.format(plugin_name), 404

    plugin_config.load_from_json(config_json)
    plugin_config.commit()
    return jsonify(config_json), 200


@internal_ip_required()
def put_plugin_config():
    if 'plugin_name' not in request.json:
        return '\'plugin_name\' is empty', 400
    plugin_name = request.json['plugin_name']

    if 'config' not in request.json:
        return '\'config\' is empty', 400
    new_config_json = request.json['config']

    plugin_config = None
    for config_class in ConfigModelRegister.all_plugin_config:
        if config_class.__plugin_name__ == plugin_name:
            plugin_config = config_class()
            break

    if plugin_config is None:
        return 'plugin \'{0}\' not exists'.format(plugin_name), 404

    for key, value in new_config_json.items():
        if hasattr(plugin_config, key):
            setattr(plugin_config, key, value)

    plugin_config.commit()
    return '', 200
