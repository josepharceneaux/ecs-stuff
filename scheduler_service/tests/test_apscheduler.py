"""
Test cases for APScheduler code.
"""
import datetime
from time import sleep
import pytest


def add_job_callback():
    """
    Temporary callback function called when job time is up.
    :return:
    """
    pass


@pytest.mark.usefixtures('apscheduler_setup')
class TestAPScheduler:
    """
    Test class that includes tests for:
    - adding a job
    - removing a job
    - get a job
    - adding bulk jobs
    - removing bulk jobs
    """

    def test_scheduler_job_add(self, apscheduler_setup):
        """
        Create and add job in scheduler
        :param apscheduler_setup: start the scheduler
        :return:
        """
        job = apscheduler_setup.add_job(add_job_callback)
        assert apscheduler_setup.get_job(job_id=job.id).id == job.id

    def test_scheduler_job_remove(self, apscheduler_setup):
        """
        Create and add job and then remove job using job id
        :param apscheduler_setup:
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job = apscheduler_setup.add_job(add_job_callback,
                                        start_date=start_date,
                                        end_date=end_date,
                                        trigger='interval'
                                                 )
        apscheduler_setup.remove_job(job_id=job.id)
        assert apscheduler_setup.get_job(job_id=job.id) is None

    def test_scheduler_get_job(self, apscheduler_setup):
        """
        Create job and then get it using job id
        :param apscheduler_setup:
        :return:
        """
        job = apscheduler_setup.add_job(add_job_callback)
        assert apscheduler_setup.get_job(job_id=job.id) == job

    def test_scheduler_jobs_add(self, apscheduler_setup):
        """
        Create and add jobs in scheduler in bulk and check if job is added one by one
        :param apscheduler_setup:
        :return:
        """
        jobs = []
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        for i in range(3):
            jobs.append((apscheduler_setup.add_job(add_job_callback,
                                                   start_date=start_date,
                                                   end_date=end_date,
                                                   trigger='interval'
                                                            )).id)
            sleep(1)

        for job_id in jobs:
            assert apscheduler_setup.get_job(job_id=job_id).id == job_id

    def test_scheduler_jobs_remove(self, apscheduler_setup):
        """
        Add the jobs and then remove all of them. then check if they are nomore.
        :param apscheduler_setup:
        :return:
        """
        jobs = []
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        for i in range(10):
            jobs.append(apscheduler_setup.add_job(add_job_callback,
                                                  start_date=start_date,
                                                  end_date=end_date,
                                                  trigger='interval'
                                                           ).id)
        apscheduler_setup.remove_all_jobs()

        for job_id in jobs:
            assert apscheduler_setup.get_job(job_id=job_id) is None

