import redis
from .config import RedisConfig
import json


class RedisClient(object):
    def __init__(self, host=None, port=None, max_connections=2000, auth=None, db=None):
        # 使用全局配置初始化 redis
        if host is None and port is None and auth is None and db is None:
            config = RedisConfig()
            host = config.redis_host
            port = config.redis_port
            auth = config.redis_auth
            db = config.redis_db
        # 初始化redis链接
        if auth is None or len(auth.strip()) == 0:
            auth = None
        self._connection = redis.StrictRedis(connection_pool=self.create_pool(host, port, max_connections, db, auth))

    @staticmethod
    def create_pool(host, port, max_connections, db=0, auth=None):
        # 设置redis连接池
        return redis.ConnectionPool(
            max_connections=max_connections,
            host=host,
            port=port,
            db=db,
            password=auth)

    def set_data(self, key, value, ex=None, nx=False):
        return self._connection.set(key, value, ex, None, nx)

    def get_data(self, key):
        return self._connection.get(key)

    def del_data(self, key):
        return self._connection.delete(key)

    def zrange_by_score_data(self, key, min_value, max_value, offset=None, count=None):
        return self._connection.zrangebyscore(key, min_value, max_value, offset, count)

    def flush_db(self):
        self._connection.flushdb()

    def hgetall(self, name):
        hget_result = dict(self._connection.hgetall(name))
        # 处理取出的二进制数据并且转成str重新赋值
        return_result = dict()
        for k in hget_result:
            key = bytes.decode(k)
            value = bytes.decode(hget_result.get(k))
            return_result[key] = value
        return return_result

    def hset(self, name, key, value):
        self._connection.hset(name, key, value)

    def hmset(self, key, value, ex=0):
        self._connection.hmset(key, value)
        if ex > 0:
            self._connection.expire(key, ex)

    def get_connection(self):
        return self._connection

    def set_json(self, key, json_value, ex):
        json_str = json.dumps(json_value)
        return self._connection.set(key, json_str, ex)

    def get_json(self, key):
        json_str = self._connection.get(key)
        if json_str is None:
            return None
        json_value = json.loads(json_str)
        return json_value

    def subscribe(self, channel_name):
        """
        redis订阅某个channel
        :param channel_name: 频道名称
        """
        try:
            pub = self._connection.pubsub()
            pub.subscribe(channel_name)
        except Exception as _:
            return None

        return pub

    def publish(self, channel_name, msg):
        """
        redis在channel_name中发布消息msg
        :param channel_name: 频道名称
        :param msg: 消息
        """
        self._connection.publish(channel_name, msg)
        return True
