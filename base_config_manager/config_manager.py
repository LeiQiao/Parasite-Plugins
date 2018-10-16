import pa
from .models import Configuration
import json


# 获取插件配置项
def get_plugin_config(plugin_name):
    plugin_config = Configuration.query.filter_by(plugin_name=plugin_name).first()
    if (plugin_config is None) or (len(plugin_config.config_json) == 0):
        return None
    return json.loads(plugin_config.config_json)


def set_plugin_config(plugin_name, config_json):
    if config_json is None:
        config_json = ''
    if not isinstance(config_json, str):
        config_json = json.dumps(config_json)

    plugin_config = Configuration.query.filter_by(plugin_name=plugin_name).first()
    if plugin_config is None:
        plugin_config = Configuration(plugin_name=plugin_name, config_json=config_json)
        pa.database.session.add(plugin_config)
    else:
        plugin_config.config_json = config_json
    pa.database.session.commit()
