import redis


class RedisClient(object):
    def __init__(self, host, port, max_connections=2000, auth=None, db=0):
        # 初始化redis链接
        if auth is None or auth.strip() is '':
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
