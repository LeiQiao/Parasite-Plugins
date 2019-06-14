from pa.plugin import Plugin
from .record_api_config import RecordAPIConfig
import pa


class RecordApiPlugin(Plugin):
    __pluginname__ = 'record_api'

    def on_load(self):
        config = RecordAPIConfig()
        pa.web_app.config['JSON_AS_ASCII'] = not config.chinese_json
