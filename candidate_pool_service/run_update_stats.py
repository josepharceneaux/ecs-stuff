from datetime import datetime
from candidate_pool_service.candidate_pool_app import logger
from candidate_pool_service.candidate_pool_app import redis_store
from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import (update_smartlist_stats,
                                                                                        update_talent_pool_stats,
                                                                                        update_talent_pipeline_stats)

stats_update_key = 'stats-update-timestamp-%s' % datetime.utcnow().date().strftime('%m/%d/%Y')

if not redis_store.exists(stats_update_key):
    redis_store.setex(stats_update_key, 86400)
    logger.info("CRON JOB: Stats update process has been started")

    update_smartlist_stats.delay()
    update_talent_pool_stats.delay()
    update_talent_pipeline_stats.delay()