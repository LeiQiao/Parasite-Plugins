from .config_model import ConfigModel
from .base_plugin import BasePlugin
import pa


class BaseConfig(ConfigModel):
    __configname__ = 'base'

    db_uri = ConfigModel.Column()
    create_tables = ConfigModel.Column(True)

    def on_changed(self, key, value):
        if key == BaseConfig.create_tables:
            BasePlugin.__create_table = value


class ServerConfig(ConfigModel):
    __configname__ = 'server'

    ip = ConfigModel.Column('0.0.0.0')
    port = ConfigModel.Column(5001)

    def on_changed(self, key, value):
        if key == ServerConfig.ip:
            pa.server_ip = value
        elif key == ServerConfig.port:
            pa.server_port = value
