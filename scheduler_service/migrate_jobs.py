from scheduler_service import redis_store, scheduler, logger


def migrate_sched_jobs():
    jobs = scheduler.get_jobs()

    for job in jobs:
        try:
            if not job.name == 'run_job':
                pass
            redis_store.rpush('apscheduler_job_ids:{0}'
                            .format('user_%s' % job.args[0] if job.args and job.args[0] else 'general_%s' % job.name), job.id)
        except Exception as ex:
            logger.error('Message: {0}, User_ID: {1}, Job_ID: {2}, Job_Name: {3}'
                         .format(ex.message, job.args[0] if job.args else None,
                                   job.id, job.name))
