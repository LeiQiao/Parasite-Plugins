import pa
from pa.plugin import Plugin
import getopt
import sys
import os
from fishbase.fish_common import conf_as_dict
from fishbase.fish_file import check_sub_path_create
from fishbase.fish_logger import logger as fishbase_logger, set_log_file
from .plugin_manager import PluginManager
from .server_config import ServerConfig


class BasePlugin(Plugin):
    def __init__(self, **kwargs):
        super(BasePlugin, self).__init__(**kwargs)
        if pa.plugin_manager is not None and pa.plugin_manager.get_plugin('base') is not None:
                raise ValueError('realloc base plugin')
        # 默认创建数据库中不存在的表

    def on_load(self):
        self.start_log_service()
        self.load_config()

    @staticmethod
    def start_log_service():
        # 创建必须的log文件夹
        check_sub_path_create('log')
        # 日志文件路径
        set_log_file(os.path.join(os.path.abspath('log'), 'server.log'))
        pa.log = fishbase_logger
        # add stdout log output
        import logging
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        # 捕捉异常
        sys.excepthook = BasePlugin.handle_exception

    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        pa.log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    def load_config(self):
        opts, args = getopt.getopt(sys.argv[1:], 'c:', ['debug', 'extra_plugin='])

        # 调试状态
        if 'debug' in args:
            pa.debug = True

        config_file = None
        extra_plugins = []
        for opt in opts:
            if opt[0] == '-c':
                config_file = opt[1]
            elif opt[0] == '--extra_plugin':
                extra_plugins = opt[1].split(',')
        if config_file is None:
            pa.log.info('Base: no config file.')
            return

        success, config_info, _ = conf_as_dict(config_file)
        if not success:
            raise ValueError('config file format error.')

        # 插件的配置项
        if pa.plugin_config is None:
            pa.plugin_config = {}
        for key in config_info.keys():
            pa.plugin_config[key] = {}
            for conf_key, conf_value in config_info[key].items():
                pa.plugin_config[key][conf_key] = conf_value

        # 加载插件
        if pa.plugin_manager is None:
            pa.plugin_manager = PluginManager()

        # 将 base 加入到插件列表中
        pa.plugin_manager.start(self, os.path.dirname(__file__))

        # 调试插件
        for extra_plugin in extra_plugins:
                pa.plugin_manager.load_extra_plugin(extra_plugin.strip())

        # 设置 Parasite 服务的 IP 和端口
        sc = ServerConfig()
        pa.server_ip = sc.ip
        pa.server_port = sc.port

    # 获取模块所在 sys.modules 中的名称
    @staticmethod
    def get_module_name(plugin):
        module_name = plugin.__module__.split('.')[:-1]
        reversed_module_name = reversed(module_name)
        for name in reversed_module_name:
            if name != plugin.plugin_name:
                module_name = module_name[:-1]
            else:
                break
        module_name = '.'.join(module_name)
        return module_name
