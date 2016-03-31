__author__ = 'ufarooqi'
from flask.ext.redis import FlaskRedis
from redis_collections import Dict

redis_store = FlaskRedis()


def redis_dict(redis_instance, redis_list_key=None):
    if redis_list_key and redis_instance.exists(redis_list_key):
        return Dict(redis=redis_instance, key=redis_instance.get(redis_list_key))
    else:
        redis_list_instance = Dict(redis=redis_instance)
        if redis_list_key:
            redis_instance.set(redis_list_key, redis_list_instance.key)
        return redis_list_instance
