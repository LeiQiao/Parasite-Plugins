import pa
import json


class ConfigModelRegister(type):
    all_plugin_config = []
    config_operator = None

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
            pa.log.warning('Base: config class \'{0}\' do NOT have __configname__'.format(self.__class__.__name__))
            return
        # 获取原始配置信息
        if self.__configname__ in pa.plugin_config:
            self.load_from_json(pa.plugin_config[self.__configname__])
        else:
            self.load_from_json({})

    def synchronize(self):
        if self.__configname__ not in pa.plugin_config:
            pa.plugin_config[self.__configname__] = {}

        for config_item_name, config_item_column in vars(self.__class__).items():
            if not isinstance(config_item_column, ConfigModel.Column):
                continue

            config_item_value = config_item_column.default
            if not isinstance(getattr(self, config_item_name), ConfigModel.Column):
                config_item_value = getattr(self, config_item_name)
            pa.plugin_config[self.__configname__][config_item_name] = config_item_value

    # Overridable -- handle config changed event
    @staticmethod
    def on_changed(key, value):
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
            elif not isinstance(getattr(self, config_item_name), ConfigModel.Column):
                # 如果新的 json 中没有该 key，并且该 key 已经被设置过则不设置默认值
                continue

            notify = False
            # 第一次设置不需要通知配置变更
            if not isinstance(getattr(self, config_item_name), ConfigModel.Column):
                notify = True
            setattr(self, config_item_name, config_item_value)
            if notify:
                self.__class__.on_changed(config_item_column, config_item_value)

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
            return ConfigModel.bool_to_str
        elif isinstance(default, int):
            return str
        elif isinstance(default, list) or isinstance(default, dict):
            return json.dumps
        else:
            pa.log.warning('Base: unable found best serializer for type {0}'.format(type(default)))
            return None

    @staticmethod
    def best_deserializer(default):
        if default is None:
            return None
        elif isinstance(default, str):
            return None
        elif isinstance(default, bool):
            return ConfigModel.str_to_bool
        elif isinstance(default, int):
            return int
        elif isinstance(default, list) or isinstance(default, dict):
            return json.loads
        else:
            pa.log.warning('Base: unable found best deserializer for type {0}'.format(type(default)))
            return None

    @staticmethod
    def bool_to_str(b):
        return '1' if b else '0'

    @staticmethod
    def str_to_bool(s):
        return True if s is not None and s == '1' else False


class ConfigOperator:

    # Overridable -- handle load config event
    @staticmethod
    def load(config_model_name):
        pass

    # Overridable -- handle save config event
    @staticmethod
    def save(config_model):
        pass

    # Overridable -- handle first load config
    @staticmethod
    def update_all_config():
        pass
