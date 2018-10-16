from . import config_manager
import pa


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
            self.serializer = serializer
            self.deserializer = deserializer

    __plugin_name__ = None

    def __init__(self):
        if self.__plugin_name__ is None:
            return
        # 获取原始配置信息
        if self.__plugin_name__ in pa.plugin_config:
            self.load_from_json(pa.plugin_config[self.__plugin_name__])
        saved_config = config_manager.get_plugin_config(self.__plugin_name__)
        if saved_config is None:
            saved_config = {}
        self.load_from_json(saved_config)

    def commit(self):
        save_config = self.dump_to_json()
        config_manager.set_plugin_config(self.__plugin_name__, save_config)

    def load_from_json(self, config_json):
        for config_item_name, config_item_column in vars(self.__class__).items():
            if not isinstance(config_item_column, ConfigModel.Column):
                continue

            config_item_value = config_item_column.default
            if config_item_name in config_json:
                config_item_value = config_json[config_item_name]

            if config_item_column.serializer is not None:
                config_item_value = config_item_column.serializer(config_item_value)
            setattr(self, config_item_name, config_item_value)

    def dump_to_json(self):
        config_json = {}
        for config_item_name, config_item_column in vars(self.__class__).items():
            if not isinstance(config_item_column, ConfigModel.Column):
                continue

            config_item_value = getattr(self, config_item_name)
            if config_item_value == config_item_column:
                config_item_value = config_item_column.default

            if config_item_column.deserializer is not None:
                config_item_value = config_item_column.deserializer(config_item_value)
            config_json[config_item_name] = config_item_value
        return config_json
