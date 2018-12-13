from .config_model import ConfigModel


class ServerConfig(ConfigModel):
    __configname__ = 'server'

    ip = ConfigModel.Column('0.0.0.0')
    port = ConfigModel.Column(5001)
