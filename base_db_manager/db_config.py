from plugins.base.config_model import ConfigModel


DATABASE_ENGINE_FLASK_SQLALCHEMY = 'flask-sqlalchemy'
DATABASE_ENGINE_SQLALCHEMY = 'sqlalchemy'

class DBConfig(ConfigModel):
    __configname__ = 'base_db_manager'

    db_uri = ConfigModel.Column('sqlite:///db/Parasite.sqlite')
    database_engine = ConfigModel.Column(DATABASE_ENGINE_FLASK_SQLALCHEMY)
    create_table = ConfigModel.Column(True)
