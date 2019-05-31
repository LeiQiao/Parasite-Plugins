from base.config_model import ConfigModel


class RedisConfig(ConfigModel):
    __configname__ = 'redis_client'

    redis_host = ConfigModel.Column('')
    redis_port = ConfigModel.Column('')
    redis_auth = ConfigModel.Column('')
    redis_db = ConfigModel.Column(0)
