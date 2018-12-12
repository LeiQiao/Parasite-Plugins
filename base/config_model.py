import pa
import json


class ConfigModelRegister(type):
    all_plugin_config = []

    def __init__(cls, name, bases, clsdict):
        super(ConfigModelRegister, cls).__init__(name, bases, clsdict)
        if len(bases) > 0 and ConfigModel in bases:
            ConfigModelRegister.all_plugin_config.append(cls)


class ConfigModel(metaclass=ConfigModelRegister):
    class Column:
        def __init__(self, default=None, serializer=None, deserializer=None):
            self.default = default

            if serializer is None:
                serializer = ConfigModel.best_serializer(default)
            if deserializer is None:
                deserializer = ConfigModel.best_deserializer(default)

            self.serializer = serializer
            self.deserializer = deserializer

    __configname__ = None

    def __init__(self):
        if self.__configname__ is None:
            return
        # 获取原始配置信息
        if self.__configname__ in pa.plugin_config:
            self.load_from_json(pa.plugin_config[self.__configname__])

    # Overridable -- handle config changed event
    def on_changed(self, key, value):
        pass

    def load_from_json(self, config_json):
        for config_item_name, config_item_column in vars(self.__class__).items():
            if not isinstance(config_item_column, ConfigModel.Column):
                continue

            config_item_value = config_item_column.default
            if config_item_name in config_json:
                config_item_value = config_json[config_item_name]

            if config_item_column.deserializer is not None:
                config_item_value = config_item_column.deserializer(config_item_value)
            notify = False
            # 第一次设置不需要通知配置变更
            if not isinstance(getattr(self, config_item_name), ConfigModel.Column):
                notify = True
            setattr(self, config_item_name, config_item_value)
            if notify:
                self.on_changed(config_item_column, config_item_value)

    def dump_to_json(self):
        config_json = {}
        for config_item_name, config_item_column in vars(self.__class__).items():
            if not isinstance(config_item_column, ConfigModel.Column):
                continue

            config_item_value = getattr(self, config_item_name)
            if config_item_value == config_item_column:
                config_item_value = config_item_column.default

            if config_item_column.serializer is not None:
                config_item_value = config_item_column.serializer(config_item_value)
            config_json[config_item_name] = config_item_value
        return config_json

    @staticmethod
    def best_serializer(default):
        if default is None:
            return None
        elif isinstance(default, str):
            return None
        elif isinstance(default, bool):
            return str
        elif isinstance(default, int):
            return str
        elif isinstance(default, list) or isinstance(default, dict):
            return json.dumps
        else:
            pa.log.warning('unable found best serializer for type {0}'.format(type(default)))
            return None

    @staticmethod
    def best_deserializer(default):
        if default is None:
            return None
        elif isinstance(default, str):
            return None
        elif isinstance(default, bool):
            return bool
        elif isinstance(default, int):
            return int
        elif isinstance(default, list) or isinstance(default, dict):
            return json.loads
        else:
            pa.log.warning('unable found best deserializer for type {0}'.format(type(default)))
            return None
