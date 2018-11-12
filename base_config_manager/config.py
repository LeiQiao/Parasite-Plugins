from .config_model import ConfigModel


class ServerConfig(ConfigModel):
    __plugin_name__ = 'server'

    # 接口所在 IP
    ip = ConfigModel.Column()
    # 接口端口号
    port = ConfigModel.Column()


class APIWrapperConfig(ConfigModel):
    __plugin_name__ = 'base_api_wrapper'

    # 来源 IP 的头域
    real_ip_header = ConfigModel.Column()
    # 内部 IP 白名单
    internal_ip_list = ConfigModel.Column()
