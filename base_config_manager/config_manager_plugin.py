from pa.plugin import Plugin
import pa
from .config import ServerConfig, APIWrapperConfig


class ConfigManagerPlugin (Plugin):
    def on_load(self):
        super(ConfigManagerPlugin, self).on_load()

        # 重新加载 base 的配置
        server_config = ServerConfig()
        if server_config.ip is not None:
            pa.server_ip = server_config.ip
        if server_config.port is not None:
            pa.server_port = server_config.port

        # 重新加载 base_api_wrapper 的配置
        api_wrapper_config = APIWrapperConfig()
        if api_wrapper_config.real_ip_header is not None:
            pa.plugin_config[api_wrapper_config.__plugin_name__]['real_ip_header'] = \
                api_wrapper_config.real_ip_header
        if api_wrapper_config.internal_ip_list is not None:
            pa.plugin_config[api_wrapper_config.__plugin_name__]['internal_ip_list'] = \
                api_wrapper_config.internal_ip_list
