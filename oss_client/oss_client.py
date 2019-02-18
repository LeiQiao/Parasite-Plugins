import pa
import oss2
import time


class OSSClient:
    def __init__(self, upload_end_point, download_end_point, key_id, key_secret, bucket_name):
        self.upload_end_point = upload_end_point
        self.download_end_point = download_end_point
        self.key_id = key_id
        self.key_secret = key_secret
        self.bucket_name = bucket_name

    # 将文件上传至阿里云 OSS
    def upload_file(self, file, file_name, private=True, retry_times=1, retry_interval=100):
        # 开始上传文件
        for retry_time in range(retry_times):
            try:
                auth = oss2.Auth(self.key_id, self.key_secret)
                bucket = oss2.Bucket(auth, self.upload_end_point, self.bucket_name)
                result = bucket.put_object(file_name, file, headers={
                    'x-oss-object-acl': 'private' if private else 'public-read'
                })
                # 如果返回值不等于 2xx 则表示失败
                if result.status < 200 or result.status > 299:
                    time.sleep(retry_interval)
                    continue
                return True
            except Exception as e:
                pa.log.error('oss_client: upload file error. retry: {0}/{1} {2}'.format(str(retry_time + 1), str(retry_times), e))
                time.sleep(retry_interval)
                continue

        # 到达重试次数还没有上传成功
        return False

    # 获取阿里云 OSS 的临时下载地址
    def get_file_url(self, file_name, expires):
        # 获取文件的临时下载地址
        try:
            auth = oss2.Auth(self.key_id, self.key_secret)
            bucket = oss2.Bucket(auth, self.download_end_point, self.bucket_name)
            acl = bucket.get_object_acl(file_name).acl
            if acl == 'public-read':
                file_url = self.get_public_download_url(file_name)
            else:
                file_url = bucket.sign_url('GET', file_name, expires)
        except Exception as e:
            pa.log.error('oss_client: get file url error.', e)
            return None

        return file_url

    # 从阿里云 OSS 中下载文件
    def download_file(self, file_name):
        # 获取文件的临时下载地址
        try:
            auth = oss2.Auth(self.key_id, self.key_secret)
            bucket = oss2.Bucket(auth, self.upload_end_point, self.bucket_name)
            remote_stream = bucket.get_object(file_name)
        except Exception as e:
            pa.log.error('oss_client: download file error: \n{0}'.format(e))
            return None

        return remote_stream

    def delete_file(self, file_name):
        # 删除文件
        try:
            auth = oss2.Auth(self.key_id, self.key_secret)
            bucket = oss2.Bucket(auth, self.upload_end_point, self.bucket_name)
            result = bucket.delete_object(file_name)
            # 如果返回值不等于 2xx 则表示失败
            if result.status < 200 or result.status > 299:
                return False
        except Exception as e:
            pa.log.error('oss_client: delete file error: \n{0}'.format(e))
            return False
        return True

    def get_public_download_url(self, file_name):
        file_url = ''
        if self.download_end_point[:7].lower() != 'http://' and self.download_end_point[:8].lower() != 'https://':
            file_url += 'https://' + self.bucket_name + '.'
        file_url += self.download_end_point + '/' + file_name
        return file_url
