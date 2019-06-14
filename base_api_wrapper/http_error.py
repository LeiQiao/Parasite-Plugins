from flask import jsonify as flask_jsonify, request as http_request
import pa


class CustomResponseCode:
    def __init__(self, code, message):
        self.code = code
        self.message = message


# 处理 http 请求各类错误情况，参考 CustomFlaskErr，去除 Flask 对象，使用 CustomResponseCode 为 J_MSG 解耦
class CustomHTTPError(Exception):
    status_code = 400

    def __init__(self, response_code=None, status_code=None):
        Exception.__init__(self)

        self.response_code = response_code

        if status_code is not None:
            self.status_code = status_code

    def jsonify(self):
        if self.response_code is None:
            return ''
        if isinstance(self.response_code, CustomResponseCode):
            return flask_jsonify({
                'return_code': self.response_code.code,
                'message': self.response_code.message
            })
        else:
            return self.response_code


# flask 错误处理，装饰器来控制使用 CustomHTTPError
@pa.web_app.errorhandler(CustomHTTPError)
def handle_http_error(error):

    # response 的 json 内容为自定义错误代码和错误信息
    response = error.jsonify()

    # response 返回 error 发生时定义的标准错误代码
    status_code = error.status_code

    # log 错误信息
    if status_code != 200:
        if isinstance(error.response_code, CustomResponseCode):
            message = error.response_code.message
        elif error.response_code is None:
            message = ''
        else:
            message = str(error.response_code)
        
        pa.log.error('%s %s %s \"%s\"',
                     http_request.method,
                     http_request.path,
                     status_code,
                     message)

    return response, status_code


# 500 服务器错误
class HTTPSystemError(CustomHTTPError):
    def __init__(self, response_code=None):
        CustomHTTPError.__init__(self, response_code, 500)


# 400 参数错误
class HTTPParameterError(CustomHTTPError):
    def __init__(self, response_code=None):
        CustomHTTPError.__init__(self, response_code, 400)


# 401 认证失败
class HTTPAuthorizationError(CustomHTTPError):
    def __init__(self, response_code=None):
        CustomHTTPError.__init__(self, response_code, 401)


# 404 资源找不到
class HTTPNotFoundError(CustomHTTPError):
    def __init__(self, response_code=None):
        CustomHTTPError.__init__(self, response_code, 404)


# 302 重定向
class HTTPRedirectError(CustomHTTPError):
    def __init__(self, response_code=None):
        CustomHTTPError.__init__(self, response_code, 302)


# 自定义成功
def custom_success(ret_object=None, message='成功', status_code=200):
    return_json = {
        'return_code': '90000',
        'message': message
    }

    if ret_object is not None:
        return_json['data'] = ret_object

    return flask_jsonify(return_json), status_code


def parameter_error(error_message='参数错误'):
    return HTTPParameterError(CustomResponseCode(90100, error_message))


def authorization_error(error_message='UNAUTHORIZAED'):
    return HTTPAuthorizationError(CustomResponseCode(90101, error_message))
