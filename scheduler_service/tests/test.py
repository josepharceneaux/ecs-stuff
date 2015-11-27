from time import sleep
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler_service.tasks import app
import unittest

__author__ = 'saad'


"""
Callback method for APScheduler job
"""


def add_job_callback():
    pass


"""

SchedulingService test cases
Add Job
Get Job
Resume Job
Stop Job
Bulk add and remove jobs

"""


class SchedulingServiceTestCase(unittest.TestCase):
    def setUp(self):
        """
        Setup APScheduler, jobstore, executor and start apscheduler
        :return:
        """
        app.config['TESTING'] = True
        self.app = app.test_client()
        job_store = RedisJobStore()
        jobstores = {
            'redis': job_store
        }
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        self.scheduler = BackgroundScheduler(jobstore=jobstores, executors=executors)
        self.scheduler.add_jobstore(jobstore=job_store)
        self.scheduler.start()

    def test_scheduler_job_add(self):
        """
        Add job to APScheduler jobstore
        :return:
        """
        job = self.scheduler.add_job(add_job_callback)
        assert self.scheduler.get_job(job_id=job.id) == job

    def test_scheduler_job_remove(self):
        """
        Remove job from APScheduler jobstore
        :return:
        """
        job = self.scheduler.add_job(add_job_callback)
        self.scheduler.remove_job(job_id=job.id)
        assert self.scheduler.get_job(job_id=job.id) == None

    def test_scheduler_get_job(self):
        """
        Get job from APScheduler
        :return:
        """
        job = self.scheduler.add_job(add_job_callback)
        assert self.scheduler.get_job(job_id=job.id) == job

    def test_scheduler_jobs_add(self):
        jobs = []
        for i in range(3):
            j = self.scheduler.add_job(add_job_callback,
                                       trigger='interval')
            jobs.append(j.id)
            sleep(1)

        for job in jobs:
            assert self.scheduler.get_job(job_id=job).id == job

    def test_scheduler_jobs_remove(self):
        jobs = []
        for i in range(10):
            jobs.append(self.scheduler.add_job(add_job_callback).id)

        self.scheduler.remove_all_jobs()

        for job_id in jobs:
            assert self.scheduler.get_job(job_id=job_id) is None

    def tearDown(self):
        self.scheduler.remove_all_jobs()
        self.scheduler.shutdown()

if __name__ == '__main__':
    unittest.main()
