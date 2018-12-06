from functools import wraps
from flask import request
import pa
import os


def internal_ip_required():
    def decorated(func):
        @wraps(func)
        def wrapper(**kwargs):
            plugin_name = os.path.basename(os.path.dirname(__file__))
            # 判断请求是否为内网地址
            if pa.plugin_config[plugin_name]['real_ip_header'] in request.headers:
                real_ip = request.headers[pa.plugin_config[plugin_name]['real_ip_header']]
            else:
                real_ip = request.remote_addr
            # 判断是否内部 IP 地址访问，如果不是则返回鉴权失败
            if real_ip == '127.0.0.1' or real_ip == '0.0.0.0':
                pass
            else:
                real_ip_sction = real_ip.split('.')
                visitor_ip_allowed = False
                for allow_ip in pa.plugin_config[plugin_name]['internal_ip_list']:
                    allow_ip_section = allow_ip.strip().split('.')
                    if len(allow_ip_section) != 4:
                        continue
                    ip_match = True
                    for index, ips in enumerate(allow_ip_section):
                        if ips == '*':
                            continue
                        if real_ip_sction[index] != ips:
                            ip_match = False
                            break
                    if ip_match:
                        visitor_ip_allowed = True
                        break
                if not visitor_ip_allowed:
                    return 'visitor ip not allowed', 401
            return func(**kwargs)
        return wrapper
    return decorated
