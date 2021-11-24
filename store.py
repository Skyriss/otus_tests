import logging
from datetime import datetime, timedelta
from time import sleep

import redis

REDIS_HOST = "localhost"
REDIS_PORT = "60722"
MIN_DELAY = 0.1
TRY_NUM = 3

def retry(func):
    def wrapper(*args, **kwargs):
        for try_id in range(TRY_NUM):
            try:
                return func(*args, **kwargs)
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as ex:
                logging.info("Could not connect to Redis. Retrying.")
            sleep(MIN_DELAY * (try_id + 1))
        logging.error("Redis is not responding")
        raise ConnectionError("Connection failed after %i tries" % (TRY_NUM,))
    return wrapper


class Storage:

    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.host = host
        self.port = port
        self.redis = None

    @retry
    def connect(self):
        self.redis = redis.Redis(self.host, self.port, decode_responses=True)

    @retry
    def get(self, key):
        logging.info("Trying to get '%s' value from cache", key)
        value = self.redis.get(key)
        if value:
            return value.decode()
        return value


    @retry
    def set(self, key, value, expire=None):
        logging.info("Trying to set '%s' value to '%s' into cache", value, key)
        if value is not None:
            self.redis.set(key, value.encode(), expire)


class Store(Storage):

    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.cache = {}


    def cache_get(self, key):
        cached_value = self.cache.get(key)
        if cached_value and cached_value["expire"] > datetime.now():
            return cached_value["value"]
        return None

    def cache_set(self, key, value, expire=60*60):
        self.cache.update({key: {"value": value, "expire": datetime.now() + timedelta(seconds=expire)}})

