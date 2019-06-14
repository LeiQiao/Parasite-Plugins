from flask import request, Response
from .config import LDAPUserConfig
from base_api_wrapper.http_error import *
from .i18n import *
import uuid
from redis_client.redis_client import RedisClient
from .tools.verify_code import VerifyCode
from ldap_user.user import LDAPUser
from datetime import datetime, timedelta
import ldap


SESSION_PREFIX = 'user_session_'


def session():
    ldap_config = LDAPUserConfig()
    redis = RedisClient()

    # 生成 session
    session_id = SESSION_PREFIX + str(uuid.uuid1()).replace('-', '')

    # 生成随机验证码图片
    vcode = VerifyCode()
    if ldap_config.debug_captcha is not None:
        vcode.text = ldap_config.debug_captcha
    captcha_info = vcode.gen_code()
    image_file = captcha_info['image_file']
    image_content = image_file.getvalue()
    image_file.close()

    user_session = {
        'captcha': captcha_info['code']
    }
    redis.set_json(session_id, user_session, ldap_config.unlogin_session_expire)

    resp = Response(image_content, mimetype='jpeg')
    expire_timestamp = (datetime.now() + timedelta(seconds=ldap_config.unlogin_session_expire)).timestamp()
    resp.set_cookie('session_id', session_id, expires=expire_timestamp)

    return resp


def login():
    # 获取参数
    user_name = request.form.get('user_name', None)
    password = request.form.get('password', None)
    captcha = request.form.get('captcha', None)

    session_id = request.cookies.get('session_id', None)

    if user_name is None or len(user_name) == 0 or \
       password is None or len(password) == 0:
        raise authorization_error(i18n(USER_PASSWORD_ERROR))

    if captcha is None or len(captcha) == 0 or \
       session_id is None or len(session_id) == 0 or not session_id.startswith(SESSION_PREFIX):
        raise authorization_error(i18n(LOGIN_CAPTCHA_MISMATCH_ERROR))

    ldap_config = LDAPUserConfig()
    redis_client = RedisClient()

    # 校验验证码
    user_session = redis_client.get_json(session_id)

    if user_session is None or 'captcha' not in user_session or user_session['captcha'] != captcha:
        redis_client.del_data(session_id)
        raise authorization_error(i18n(LOGIN_CAPTCHA_MISMATCH_ERROR))

    # 校验用户名密码
    ldap_service = ldap.initialize(ldap_config.ldap_url)
    ldap_service.protocol_version = ldap.VERSION3
    try:
        ldap_service.simple_bind_s(user_name, password)
    except ldap.LDAPError:
        redis_client.del_data(session_id)
        raise authorization_error(i18n(USER_PASSWORD_ERROR))
    except Exception as e:
        pa.log.error('LDAPUserPlugin: unable request ldap server: {0}'.format(e))
        raise authorization_error(i18n(LOGIN_ERROR))

    # update user info
    cn_name = search_cn_name_from_ldap(user_name)
    user_session = {
        'user_id': user_name,
        'cn_name': cn_name if cn_name is not None else user_name
    }

    redis_client.set_json(session_id, user_session, ldap_config.logined_session_expire)

    resp, status_code = custom_success(user_session)

    # update logined session_id expires
    expire_timestamp = (datetime.now() + timedelta(seconds=ldap_config.logined_session_expire)).timestamp()
    resp.set_cookie('session_id', session_id, expires=expire_timestamp)
    return resp, status_code


def search_cn_name_from_ldap(user_name):
    ldap_config = LDAPUserConfig()
    try:
        user_name = user_name.split('@')[0]
        search_filter = '(sAMAccountName=' + user_name + ')'
        ldap_result_id = ldap_config.ldap_service.search(ldap_config.ldap_dn,
                                                         ldap.SCOPE_SUBTREE,
                                                         search_filter,
                                                         None)
        result_type, result_data = ldap_config.ldap_service.result(ldap_result_id, 0)
        if result_type == ldap.RES_SEARCH_ENTRY:
            return result_data[0][1]['cn'][0].decode('utf-8')
        else:
            return None
    except Exception as e:
        pa.log.error('LDAPUserPlugin: unable found user for user name \'{0}\': {1}'.format(user_name, e))
        return None


@LDAPUser.login_required()
def search_users():
    # login required
    LDAPUser.current_user_id()

    user_name = request.args.get('user_name', None)

    if user_name is None or len(user_name) == 0:
        raise parameter_error(i18n(USER_NAME_EMPTY_ERROR))

    ldap_config = LDAPUserConfig()

    search_user_results = []
    try:
        search_filter = '(UserPrincipalName=*' + user_name + '*)'
        users = ldap_config.ldap_service.search_s(ldap_config.ldap_dn, ldap.SCOPE_SUBTREE, search_filter, None)
        for user in users:
            search_user_results.append({
                'user_id': user[1]['mail'][0].decode('utf-8'),
                'cn_name': user[1]['cn'][0].decode('utf-8')
            })
    except Exception as e:
        pa.log.error('LDAPUserPlugin: unable users \'{0}\': {1}'.format(user_name, e))
        raise HTTPSystemError(i18n(USER_SEARCH_ERROR))

    return custom_success(search_user_results)
