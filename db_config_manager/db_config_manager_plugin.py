from pa.plugin import Plugin
from plugins.base.config_model import ConfigModelRegister
from .db_config_manager import DBConfigManager


class DBConfigManagerPlugin(Plugin):
    __pluginname__ = 'db_config_manager'

    def on_load(self):
        ConfigModelRegister.config_operator = DBConfigManager()
        ConfigModelRegister.config_operator.update_all_config()
