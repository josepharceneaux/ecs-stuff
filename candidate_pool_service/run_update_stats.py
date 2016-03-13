from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import (update_smartlist_stats,
                                                                                        update_talent_pool_stats,
                                                                                        update_talent_pipeline_stats)

from candidate_pool_service.candidate_pool_app import logger

logger.info("CRON JOB: Stats update process has been started")

update_smartlist_stats.delay()
update_talent_pool_stats.delay()
update_talent_pipeline_stats.delay()