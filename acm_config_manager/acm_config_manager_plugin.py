from pa.plugin import Plugin
from plugins.base.config_model import ConfigModelRegister
from .acm_config_manager import ACMConfigManager


class ACMConfigManagerPlugin(Plugin):
    __pluginname__ = 'acm_config_manager'

    def on_load(self):
        ConfigModelRegister.config_operator = ACMConfigManager()
        ConfigModelRegister.config_operator.update_all_config()
