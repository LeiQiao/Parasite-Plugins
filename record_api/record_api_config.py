from base.config_model import ConfigModel


class RecordAPIConfig(ConfigModel):
    __configname__ = 'record_api'

    chinese_json = ConfigModel.Column(True)
