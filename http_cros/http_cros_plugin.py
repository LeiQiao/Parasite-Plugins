from pa.plugin import Plugin
import pa
from .http_cros_config import HTTPCrosConfig


class HTTPCrosPlugin(Plugin):
    __pluginname__ = 'http_cros'


@pa.web_app.after_request
def after_request(response):
    config = HTTPCrosConfig()

    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization,session_id')
    response.headers.add('Access-Control-Allow-Methods', config.allow_methods)

    # 这里不能使用add方法，否则会出现 The 'Access-Control-Allow-Origin' header contains multiple values 的问题
    response.headers['Access-Control-Allow-Origin'] = config.allow_origin
    return response
