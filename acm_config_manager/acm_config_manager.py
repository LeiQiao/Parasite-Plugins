from plugins.base.config_model import ConfigOperator
import pa
import json
import acm
import configparser


class ACMConfigManager(ConfigOperator):

    @staticmethod
    def load(config_name):
        acm_config = ACMConfigManager._load_config_from_acm()
        if config_name not in acm_config:
            return

        if config_name not in pa.plugin_config:
            pa.plugin_config[config_name] = acm_config
            return

        for key, value in acm_config.items():
            pa.plugin_config[config_name][key] = value

    @staticmethod
    def save(config_model):
        raise SystemError('ACMConfigManager: ACM not support write config')

    @staticmethod
    def update_all_config():
        acm_config = ACMConfigManager._load_config_from_acm()
        if acm_config is None:
            return
        
        for config_name, config_dict in acm_config.items():
            if config_name not in pa.plugin_config:
                pa.plugin_config[config_name] = config_dict
                continue
            for key, value in config_dict.items():
                pa.plugin_config[config_name][key] = value

    # noinspection PyProtectedMember
    @staticmethod
    def _load_config_from_acm():
        if 'acm_config_manager' in pa.plugin_config:
            _acm = acm.ACMClient(pa.plugin_config['acm_config_manager']['end_point'],
                                 pa.plugin_config['acm_config_manager']['namespace'],
                                 pa.plugin_config['acm_config_manager']['ak'],
                                 pa.plugin_config['acm_config_manager']['sk'])
        else:
            pa.log.warning('ACM configuration not found in config file')
            return None

        config_str = _acm.get(pa.plugin_config['acm_config_manager']['data_id'],
                              pa.plugin_config['acm_config_manager']['group'])

        config_format = 'ini'
        if 'format' in pa.plugin_config['acm_config_manager']:
            config_format = pa.plugin_config['acm_config_manager']['format']

        if config_format == 'ini':
            cf = configparser.ConfigParser()
            cf.read_string(config_str)
            config_dict = dict(cf._sections)
        elif config_format == 'json':
            config_dict = json.loads(config_str)
        else:
            raise TypeError('ACMConfigManager: unknown config format \'{0}\''.format(format))

        return config_dict
