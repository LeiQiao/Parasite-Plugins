from plugins.base.config_model import ConfigModel


class DBConfig(ConfigModel):
    __configname__ = 'base_db_manager'

    db_uri = ConfigModel.Column('sqlite:///db/Parasite.sqlite')
    create_table = ConfigModel.Column(True)
