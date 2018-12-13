from plugins.base.config_model import ConfigOperator
from .models import Configuration
import pa
import json


class DBConfigManager(ConfigOperator):

    @staticmethod
    def load(config_name):
        try:
            config = Configuration.query.filter_by(config_name=config_name).first()
            if config is None:
                return
        except Exception as e:
            pa.log.error('DBConfigManager: unable fetch config \'{0}\' from database'.format(config_name))
            raise e

        config_obj = json.loads(config.config_json)
        pa.plugin_config[config_name] = config_obj

    @staticmethod
    def save(config_model):
        config_json = json.dumps(config_model.dump_to_json())
        try:
            config_obj = Configuration.query.filter_by(config_name=config_model.__configname__).first()
            if config_obj is None:
                config_obj = Configuration(config_name=config_model.__configname__, config_json=config_json)
                pa.database.session.add(config_obj)
            else:
                config_obj.config_json = config_json
            pa.database.session.commit()
        except Exception as e:
            pa.log.error('DBConfigManager: unable update config \'{0}\' to database'
                         .format(config_model.__configname__))
            raise e

    @staticmethod
    def update_all_config():
        try:
            all_config = Configuration.query.all()
        except Exception as e:
            pa.log.error('DBConfigManager: unable fetch config from database')
            raise e

        for config in all_config:
            try:
                config_obj = json.loads(config.config_json)
            except Exception as e:
                pa.log.error('DBConfigManager: unable parse config \'{0}\', format error: {1}'
                             .format(config.config_json, e))
                raise e

            if config.config_name not in pa.plugin_config:
                pa.plugin_config[config.config_name] = {}

            for key, value in config_obj.items():
                pa.plugin_config[config.config_name][key] = value
