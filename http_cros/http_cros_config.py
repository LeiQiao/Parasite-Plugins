from plugins.base.config_model import ConfigModel


class HTTPCrosConfig(ConfigModel):
    __configname__ = 'http_cros'

    allow_methods = ConfigModel.Column('GET,PUT,POST,DELETE,OPTIONS,HEAD')
    allow_origin = ConfigModel.Column('*')
