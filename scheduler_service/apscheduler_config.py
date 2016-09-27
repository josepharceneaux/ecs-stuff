from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from redis._compat import urlparse

from scheduler_service import SchedulerUtils, TalentConfigKeys
from scheduler_service.common.talent_config_manager import TalentEnvs
from scheduler_service.modules.scheduler import flask_app

__author__ = 'saad'

MAX_THREAD_POOLS = 12
LOCK_KEY = 'apscheduler_'

url = urlparse(flask_app.config[TalentConfigKeys.REDIS_URL_KEY])
if flask_app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
    job_store = RedisJobStore(db=1, host=url.hostname, password=url.password)
else:
    job_store = RedisJobStore(db=0, host=url.hostname, password=url.password)

executors = {
    'default': ThreadPoolExecutor(MAX_THREAD_POOLS),
    'processpool': ProcessPoolExecutor(max_workers=5)
}

jobstores = {
    'redis': job_store
}

job_defaults = {
    'apscheduler.job_defaults.coalesce': 'true',
    'apscheduler.job_defaults.max_instances': '1',
    'apscheduler.job_defaults.misfire_grace_time': str(SchedulerUtils.MAX_MISFIRE_TIME),
    'apscheduler.timezone': 'UTC'
}
