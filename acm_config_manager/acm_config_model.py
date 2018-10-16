import acm
import json
import pa
import configparser


class ACMConfigModel:
    class Column:
        def __init__(self, default=None, serializer=None, deserializer=None):
            self.default = default
            self.serializer = serializer
            self.deserializer = deserializer

    def __init__(self, end_point, namespace, ak, sk, data_id, group, config_format='ini'):
        self._acm = acm.ACMClient(end_point, namespace, ak, sk)
        self._acm_data_id = data_id
        self._acm_group = group
        self._config_format = config_format
        self.reload_config()
        # self._acm.add_watcher(data_id, group, self.on_acm_changed)

    # noinspection PyProtectedMember
    def reload_config(self):
        config_str = self._acm.get(self._acm_data_id, self._acm_group)
        if self._config_format == 'ini':
            cf = configparser.ConfigParser()
            cf.read_string(config_str)
            config_dict = dict(cf._sections)
            plugin_name = getattr(self, '__plugin_name__')
            if plugin_name in config_dict:
                config_dict = config_dict[plugin_name]
            else:
                config_dict = {}
        elif self._config_format == 'json':
            config_dict = json.loads(config_str)
        else:
            raise TypeError('ACMClient: unknown config format \'{0}\''.format(self._config_format))
        try:
            self.load_from_dict(config_dict)
        except Exception as e:
            pa.log.warning('ACMClient: unable load config {0}'.format(e))
            self.load_from_dict({})

    def load_from_dict(self, config_dict):
        for config_item_name, config_item_column in vars(self.__class__).items():
            if not isinstance(config_item_column, ACMConfigModel.Column):
                continue

            config_item_value = config_item_column.default
            if config_item_name in config_dict:
                config_item_value = config_dict[config_item_name]

            if config_item_column.serializer is not None:
                config_item_value = config_item_column.serializer(config_item_value)
            notify = False
            if not isinstance(getattr(self, config_item_name), ACMConfigModel.Column):
                notify = True
            setattr(self, config_item_name, config_item_value)
            if notify:
                self.on_changed(config_item_name, config_item_value)

    def on_acm_changed(self):
        self.reload_config()

    # Overridable -- handle config changed event
    def on_changed(self, key, value):
        pass
