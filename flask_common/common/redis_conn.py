import redis
from flask import current_app

try:
    redis_client = redis.Redis(host=current_app.config['REDIS_HOST'],
                                    port = current_app.config['REDIS_PORT'])
# We are running outside the application context i.e. testing so use the machine's instance.
except RuntimeError:
    redis_client = redis.Redis(host='localhost', port=6379)