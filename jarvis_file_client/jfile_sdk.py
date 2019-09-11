# -*- coding: utf-8 -*-

# 上传代码
import requests
import hmac
import hashlib
import json
import time
import os


class JFile:
    def __init__(self, app_token, app_key, url):
        self.url = url
        self.app_token = app_token
        self.app_key = app_key

        self.session = requests.Session()

    @staticmethod
    def _md5(fp):
        hash_md5 = hashlib.md5()
        fp.seek(0)
        for chunk in iter(lambda: fp.read(4096), b""):
            hash_md5.update(chunk)
        fp.seek(0)
        return hash_md5.hexdigest()

    @staticmethod
    def _pack_signature(method, param_dict):
        keys = param_dict.keys()
        keys = sorted(keys, reverse=False)
        # 拼接 key 和 value 值
        values = ''
        for key in keys:
            value = str(param_dict.get(key))
            if len(value) == 0:
                continue
            values = values + '&' + str(key) + '=' + value

        plain_text = method + values[1:]
        return plain_text

    @staticmethod
    def _raise_request_error(response):
        if response.status_code != 200:
            try:
                reason = json.loads(response.text)['message']
            except Exception as e:
                str(e)
                reason = 'System Error'
            raise ConnectionError(response.status_code, reason)

    def upload(self, file_name, remote_path=None, encrypt=False, password=None, private=True, random_name=False):
        with open(file_name, 'rb') as f:
            return self.upload_fp(f, os.path.basename(file_name), remote_path, encrypt, password, private, random_name)

    def upload_fp(self, fp, file_name, remote_path=None, encrypt=False, password=None, private=True, random_name=False):
        is_private = '1' if private else '0'
        is_random_name = '1' if random_name else '0'
        is_encrypt = '1' if encrypt else '0'
        # 拼接请求参数
        file_info = {
            'app_token': self.app_token,
            'timestamp': str(int(time.time()*1000)),
            'private': is_private,
            'random_name': is_random_name,
            'encryption': is_encrypt
        }
        if password is not None and len(password) > 0:
            file_info['encryption'] = '1'
            file_info['password'] = password
        else:
            password = ''

        if remote_path is not None and len(remote_path) > 0:
            file_info['path'] = remote_path
        else:
            remote_path = ''

        # 根据参数 key 的值 顺序拼接其 value , 实际做代码操作时, 可以使用排序方法拼接更为合适, 以下只做例子展示
        if isinstance(fp, str):
            files = open(fp, 'rb')
        else:
            files = fp
        md5_file = self._md5(files)
        files.seek(0)
        plain_text = self._pack_signature('POST', {
            'app_token': self.app_token,
            'timestamp': file_info['timestamp'],
            'files': md5_file,
            'password': password,
            'path': remote_path,
            'private': file_info['private'],
            'random_name': file_info['random_name'],
            'encryption': file_info['encryption']
        })
        # 对拼接好的字符串, 以 app_key 作为秘钥进行 hmacsha256 加密处理
        signature = hmac.new(bytes(self.app_key, 'utf8'), bytes(plain_text, 'utf8'), digestmod=hashlib.sha256)
        file_info['signature'] = signature.hexdigest()
        # 上传文件
        response = self.session.post(self.url, files={'files': (file_name, files)}, data=file_info)  # 发送请求
        print(response.headers)
        self._raise_request_error(response)
        # 返回 file-token
        ret_dict = json.loads(response.text)
        file_token = ret_dict['file_token']
        download_url = ret_dict['download_url']
        return file_token, download_url

    def get_download_url(self, file_token, expires=60000, direct_download_file=False):
        # 拼接请求参数
        file_info = {
            'app_token': self.app_token,
            'file_token': file_token,
            'expires': expires
        }
        plain_text = self._pack_signature('GET', {
            'app_token': self.app_token,
            'expires': str(expires),
            'file_token': file_token
        })
        # 对拼接好的字符串, 以 app_key 作为秘钥进行 hmacsha256 加密处理
        signature = hmac.new(bytes(self.app_key, 'utf8'), bytes(plain_text, 'utf8'), digestmod=hashlib.sha256)
        file_info['signature'] = signature.hexdigest()
        # 获取文件下载地址
        response = self.session.get(self.url, params=file_info, allow_redirects=direct_download_file)  # 发送请求
        if response.status_code == 302:
            return response.headers['Location']
        elif direct_download_file:
            self._raise_request_error(response)
            return json.loads(response.text)
        else:
            return response.content

    def download_file(self, download_url, password=None):
        if password is None:
            password = ''
        response = self.session.get(download_url, auth=('', password))
        self._raise_request_error(response)
        return response.content

    def delete_file(self, file_token, password=None):
        # 拼接请求参数
        file_info = {
            'app_token': self.app_token,
            'file_token': file_token
        }

        if password is not None and len(password) > 0:
            file_info['password'] = password
        else:
            password = ''

        plain_text = self._pack_signature('DELETE', {
            'app_token': self.app_token,
            'file_token': file_token,
            'password': password
        })
        # 对拼接好的字符串, 以 app_key 作为秘钥进行 hmacsha256 加密处理
        signature = hmac.new(bytes(self.app_key, 'utf8'), bytes(plain_text, 'utf8'), digestmod=hashlib.sha256)
        file_info['signature'] = signature.hexdigest()
        response = self.session.delete(self.url,
                                       data=file_info)
        self._raise_request_error(response)
        return True

    def get_all_share_path(self):
        # 拼接请求参数
        file_info = {
            'app_token': self.app_token
        }

        plain_text = self._pack_signature('GET', file_info)
        # 对拼接好的字符串, 以 app_key 作为秘钥进行 hmacsha256 加密处理
        signature = hmac.new(bytes(self.app_key, 'utf8'), bytes(plain_text, 'utf8'), digestmod=hashlib.sha256)
        file_info['signature'] = signature.hexdigest()
        url = self.url[:-5] + 'share'
        response = self.session.get(url, params=file_info)
        self._raise_request_error(response)
        return json.loads(response.text)

    def add_share_path(self, guest_app_token, file_path):
        # 拼接请求参数
        file_info = {
            'app_token': self.app_token,
            'guest_app_token': guest_app_token,
            'file_path': file_path
        }

        plain_text = self._pack_signature('POST', file_info)
        # 对拼接好的字符串, 以 app_key 作为秘钥进行 hmacsha256 加密处理
        signature = hmac.new(bytes(self.app_key, 'utf8'), bytes(plain_text, 'utf8'), digestmod=hashlib.sha256)
        file_info['signature'] = signature.hexdigest()
        url = self.url[:-5] + 'share/guest'
        response = self.session.post(url, data=file_info)
        self._raise_request_error(response)
        return True

    def get_share_path(self, file_path):
        # 拼接请求参数
        file_info = {
            'app_token': self.app_token,
            'file_path': file_path
        }

        plain_text = self._pack_signature('GET', file_info)
        # 对拼接好的字符串, 以 app_key 作为秘钥进行 hmacsha256 加密处理
        signature = hmac.new(bytes(self.app_key, 'utf8'), bytes(plain_text, 'utf8'), digestmod=hashlib.sha256)
        file_info['signature'] = signature.hexdigest()
        url = self.url[:-5] + 'share/guest'
        response = self.session.get(url, params=file_info)
        self._raise_request_error(response)
        return json.loads(response.text)

    def delete_share_path(self, guest_app_token, file_path):
        # 拼接请求参数
        file_info = {
            'app_token': self.app_token,
            'guest_app_token': guest_app_token,
            'file_path': file_path
        }

        plain_text = self._pack_signature('DELETE', file_info)
        # 对拼接好的字符串, 以 app_key 作为秘钥进行 hmacsha256 加密处理
        signature = hmac.new(bytes(self.app_key, 'utf8'), bytes(plain_text, 'utf8'), digestmod=hashlib.sha256)
        file_info['signature'] = signature.hexdigest()
        url = self.url[:-5] + 'share/guest'
        response = self.session.delete(url, data=file_info)
        self._raise_request_error(response)
        return True
