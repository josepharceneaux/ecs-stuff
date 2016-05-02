"""
Migration script for scheduler service jobs from old design to new design

In Old Design we get all jobs from redis and then apply multiple filters on them and then return the shortlisted jobs
to user. This procedure takes lot of time.

In New Design we store job id against each user in redis. So, that when a user requests his job he/she will get only
his/her job ids directly without filtering in python and using job ids we return all jobs of requesting user.

So, to migrate old job_ids from scheduler that are currently running to a new redis entries, we simply get jobs from
scheduler and then create list against each user entry.
"""

from scheduler_service import redis_store, scheduler, logger


def migrate_sched_jobs():
    jobs = scheduler.get_jobs()

    for job in jobs:
        try:
            key = 'apscheduler_job_ids:{0}'.format('user_%s' % job.args[0] if job.args and job.args[0] else 'general_%s' % job.name)
            if job.id not in redis_store.lrange(key, -float('Inf'), float('Inf')):
                redis_store.rpush(key, job.id)
        except Exception as ex:
            logger.error('Message: {0}, User_ID: {1}, Job_ID: {2}, Job_Name: {3}'
                         .format(ex.message, job.args[0] if job.args else None,
                                   job.id, job.name))


