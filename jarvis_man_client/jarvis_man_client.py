import pa
import json
import datetime
import requests


class JarvisManClient:
    def __init__(self, redis_client=None, jman_server_ip='https://jua.cloudpnr.com'):
        self.redis_client = redis_client
        self.token = None
        self.token_identifier = None

        if len(jman_server_ip) > 0 and jman_server_ip[-1:] == '/':
            jman_server_ip = jman_server_ip[:-1]

        self.jman_login_url = '{0}/api/v3/token'.format(jman_server_ip)
        self.jman_b_user_permission_url = '{0}/api/v3/b-user-permissions'.format(jman_server_ip)
        self.jman_b_user_permission_url_deprecated = '{0}/api/v2.0.2/b-user-permissions'.format(jman_server_ip)

        self.username = None
        self.password = None
        self.s_user_key = None

    def login(self, username, password, s_user_key=None):
        self.username = username
        self.password = password
        self.s_user_key = s_user_key
        self.token_identifier = 'jman-token-{0}'.format(username)
        self.token = None
        return self._relogin() is not None

    def __getattribute__(self, item):
        if item != 'token':
            return super(JarvisManClient, self).__getattribute__(item)

        # 如果有 redis 从 redis 中获取 token，否则从内存中获取 token
        if self.redis_client is None:
            token_json = super(JarvisManClient, self).__getattribute__(item)
        else:
            token_json = self.redis_client.get_data(self.token_identifier)
            if token_json is not None:
                token_json = token_json.decode('utf-8')
                token_json = json.loads(token_json)

        # token 不在 redis 中或内存中
        if token_json is None:
            return self._relogin()

        try:
            token = token_json['token']

            expired_datetime = datetime.datetime.strptime(token_json['expired_time'], '%Y%m%d%H%M%S')
            now_datetime = datetime.datetime.now()

            # 判断时间是否即将超时, 如果剩余时间小于 60 秒则刷新 token
            remain_second = (expired_datetime - now_datetime).seconds
            if remain_second < 60:
                return self._relogin()
            else:
                return token
        except Exception as e:
            pa.log.error('jarvis_man_client: someting wrong when get_token', e)
            # 如果异常直接刷新 token
            return self._relogin()

    def _relogin(self):
        if self.redis_client is not None:
            # 尝试获取分布式锁，如果获取到，则进行 token 刷新操作，如果没有，则返回空 token 对象
            setnx_result = self.redis_client.set_data('{0}-lock'.format(self.token_identifier), '', 10, True)
        else:
            setnx_result = True

        token = None
        # try 如果异常则直接删除锁,返回 None
        if setnx_result is True:
            try:
                # 重新获取token
                pa.log.info('jarvis_man_client: begin to get a new token')
                # 调用jman获取用户权限列表接口
                response = requests.get(self.jman_login_url, auth=(self.username, self.password))
                if response.status_code is 200:
                    resp_json = json.loads(response.text)
                    token = resp_json['token']
                    duration = int(resp_json['duration'])
                    # 组装expired_time
                    expired_time = datetime.datetime.strftime(
                        datetime.datetime.now() + datetime.timedelta(seconds=duration),
                        '%Y%m%d%H%M%S')

                    value = {'token': token, 'expired_time': expired_time}
                    if self.redis_client is not None:
                        self.redis_client.set_data(self.token_identifier, json.dumps(value), duration)
                    else:
                        self.token = value
                    pa.log.info('jarvis_man_client: new token value \'{0}\' expire at:{1}'.format(token, expired_time))
                else:
                    pa.log.error('jarvis_man_client: get new token error:{0} {1}'
                                 .format(response.status_code, response.text))
            except Exception as e:
                pa.log.error('jarvis_man_client: get new token error', e)
                if self.redis_client is not None:
                    # 直接删除锁, 等待后续有请求重新发起获取
                    self.redis_client.del_data('{0}-lock'.format(self.token_identifier))
        return token

    def get_b_user_permission_deprecated(self, app_token, user_token):
        if self.s_user_key is None:
            pa.log.error('jarvis_man_client: s_user_key is None')
            return None

        try:
            pa.log.info('jarvis_man_client: begin to get b-user permission (deprecated version)'
                        'app_token: {0} user_token: {1}'
                        .format(app_token, user_token))
            response = requests.get(self.jman_b_user_permission_url_deprecated,
                                    auth=(self.token, ''),
                                    params={'skey': self.s_user_key,
                                            'b_app_token': app_token,
                                            'b_user_token': user_token})
            if response.status_code is 200:
                # 获取用户权限列表
                resp_json = json.loads(response.text)
                pid_list = resp_json['p_id_list']
                pa.log.info('jarvis_man_client: b-user permission: {0}'.format(pid_list))
                return pid_list
            else:
                pa.log.error('jarvis_man_client: get b-user permission error:{0} {1}'
                             .format(response.status_code, response.text))
                try:
                    return_code = json.loads(response.text).get('return_code', '')
                    # 如果 return_code 为 10512 则返回签名失败的错误
                    if return_code == 10512:
                        return None
                    return []
                except Exception as e:
                    str(e)  # no used
        except Exception as e:
            pa.log.error('jarvis_man_client: b-user permission error', e)
            return None

    def get_b_user_permission(self, app_token, plain_text, signature):
        if self.s_user_key is None:
            pa.log.error('jarvis_man_client: s_user_key is None')
            return None

        try:
            pa.log.info('jarvis_man_client: begin to get b-user permission (plain_text: {0} signature: {1})'
                        .format(plain_text, signature))
            response = requests.get(self.jman_b_user_permission_url,
                                    auth=(self.token, ''),
                                    params={'skey': self.s_user_key,
                                            'b_app_token': app_token,
                                            'signature': signature,
                                            'plain_text': plain_text,
                                            'status': '01'})
            if response.status_code is 200:
                # 获取用户权限列表
                resp_json = json.loads(response.text)
                pid_list = resp_json['p_id_list']
                pa.log.info('jarvis_man_client: b-user permission: {0}'.format(pid_list))
                return pid_list
            else:
                pa.log.error('jarvis_man_client: get b-user permission error:{0} {1}'
                             .format(response.status_code, response.text))
                try:
                    return_code = json.loads(response.text).get('return_code', '')
                    # 如果 return_code 为 10512 则返回签名失败的错误
                    if return_code == 10512:
                        return None
                    return []
                except Exception as e:
                    str(e)  # no used
                    return None
        except Exception as e:
            pa.log.error('jarvis_man_client: b-user permission error', e)
            return None

    @staticmethod
    def pack_signature(method, parameters, add_empty_value=False, trim_keys=None):
        if trim_keys is None:
            trim_keys = []

        keys = parameters.keys()
        keys = sorted(keys, reverse=False)
        # 拼接 key 和 value 值
        values = ''
        for key in keys:
            if key in trim_keys:
                continue

            value = str(parameters.get(key))
            if len(value) == 0 and not add_empty_value:
                continue
            values = values + '&' + str(key) + '=' + value

        plain_text = method.upper() + values[1:]
        return plain_text


#
# from plugins.redis_client import RedisClient
# redis = RedisClient('192.168.0.206', 7380, 2000, '')
# jm = JarvisManClient(redis_client=redis, jman_server_ip='http://192.168.16.210:7095')
# jm.login('jarvis_file', 'cu763ut7', 'skey-3f467114-103c-4ff7-b7bb-66690a45b751')
#
#
# import hmac
# import hashlib
# plain_text = jm.pack_signature('GET', {
#     'a': '1',
#     'b': '2',
#     'c': '3'
# })
# signature = hmac.new(bytes('4a1d03516eaacd1eea31e7be245f78ed', 'utf8'),
#                      bytes(plain_text, 'utf8'),
#                      digestmod=hashlib.sha256).hexdigest()
# jm.get_b_user_permission('app-a8187ae7-5671-4888-4321-2cc8c4d476ba', plain_text, signature)
