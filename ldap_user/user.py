from flask import request
import functools
from redis_client import RedisClient
from base_api_wrapper.http_error import *
from ldap_user.i18n import *


class LDAPUser:
    @staticmethod
    def _get_token_by_key(key):
        token = request.headers.get('token', None)

        if token is None and request.args is not None:
            token = request.args.get('token', None)
        if token is None and request.form is not None:
            token = request.form.get('token', None)
        if token is None and request.json is not None:
            token = request.json.get('token', None)

        if token is None:
            raise authorization_error(i18n(USER_NOT_LOGIN_ERROR))

        redis_client = RedisClient()

        user_session = redis_client.get_json(token)

        if user_session is None or key not in user_session:
            raise authorization_error(i18n(USER_SESSION_EXPIRED_ERROR))

        return user_session[key]

    @staticmethod
    def current_user_id():
        return LDAPUser._get_token_by_key('user_id')

    @staticmethod
    def current_user_name():
        return LDAPUser._get_token_by_key('cn_name')

    @staticmethod
    def login_required():
        def decorated(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if LDAPUser.current_user_id():
                    return f(*args, **kwargs)
            return wrapper

        return decorated
