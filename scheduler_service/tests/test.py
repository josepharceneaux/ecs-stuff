from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler_service.tasks import app
import unittest

__author__ = 'saad'


class SchedulingServiceTestCase(unittest.TestCase):
    def setUp(self):
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
        self.scheduler.start()

    def test_scheduler_job_add(self):
        job = self.scheduler.add_job(self.add_job_callback)
        assert self.scheduler.get_job(job_id=job.id) == job

    def test_scheduler_job_remove(self):
        job = self.scheduler.add_job(self.add_job_callback)
        self.scheduler.remove_job(job_id=job.id)
        assert self.scheduler.get_job(job_id=job.id) == None

    def test_scheduler_get_job(self):
        job = self.scheduler.add_job(self.add_job_callback)
        assert self.scheduler.get_job(job_id=job.id) == job

    def test_scheduler_jobs_add(self):
        jobs = []
        for i in range(10):
            jobs.append(self.scheduler.add_job(self.add_job_callback))

        for job in jobs:
            assert self.scheduler.get_job(job_id=job.id).id == job.id

    def test_scheduler_jobs_remove(self):
        jobs = []
        for i in range(10):
            jobs.append(self.scheduler.add_job(self.add_job_callback).id)

        self.scheduler.remove_all_jobs()

        for job_id in jobs:
            assert self.scheduler.get_job(job_id=job_id) == None

    def add_job_callback(self):
        pass

    def tearDown(self):
        self.scheduler.remove_all_jobs()
        self.scheduler.shutdown()

if __name__ == '__main__':
    unittest.main()
