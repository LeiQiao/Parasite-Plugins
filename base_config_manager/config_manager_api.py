import pa
from plugins.base.config_model import ConfigModelRegister
from flask import jsonify, request
from plugins.base_api_wrapper import internal_ip_required


@internal_ip_required()
def get_plugin_config():
    try:
        config_name = request.args.get('config_name')
    except Exception as e:
        pa.log.error(e)
        config_name = None

    if config_name is None:
        return '\'config_name\' is empty', 400

    plugin_config = None
    for config_class in ConfigModelRegister.all_plugin_config:
        if config_class.__configname__ == config_name:
            plugin_config = config_class()
            break

    if plugin_config is None:
        return 'config \'{0}\' not exists'.format(config_name), 404

    config_json = plugin_config.dump_to_json()
    return jsonify(config_json), 200


@internal_ip_required()
def put_plugin_config():
    if 'config_name' not in request.json:
        return 'config_name is empty', 400
    config_name = request.json['config_name']

    if 'config' not in request.json:
        return 'config is empty', 400
    config_json = request.json['config']

    if ConfigModelRegister.config_operator is None:
        return 'can NOT write local config file', 400

    plugin_config = None
    for config_class in ConfigModelRegister.all_plugin_config:
        if config_class.__configname__ == config_name:
            plugin_config = config_class()
            break

    if plugin_config is None:
        return 'config \'{0}\' not exists'.format(config_name), 404

    plugin_config.load_from_json(config_json)

    try:
        ConfigModelRegister.config_operator.save(plugin_config)
    except Exception as e:
        pa.log.error('BaseConfigManager: {0}'.format(e))
        return str(e), 400

    plugin_config.synchronize()

    return jsonify(plugin_config.dump_to_json()), 200
