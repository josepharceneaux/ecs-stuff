import pytest

__author__ = 'saad'

"""
Test Cases for APScheduler
"""


def add_job_callback():
    """
    temporary callback function called when job time comes
    :return:
    """
    pass


@pytest.mark.usefixtures('resource_apscheduler_setup')
class TestAPScheduler:
    """
    Test class for testing add job, remove job, get job, bulk jobs added, bulk jobs removed
    """
    def test_scheduler_job_add(self, resource_apscheduler_setup):
        """
        Create and add job in scheduler
        :param resource_apscheduler_setup: start the scheduler
        :return:
        """
        job = resource_apscheduler_setup.add_job(add_job_callback)
        assert resource_apscheduler_setup.get_job(job_id=job.id) == job

    def test_scheduler_job_remove(self, resource_apscheduler_setup):
        """
        Create and add job and then remove job using job id
        :param resource_apscheduler_setup:
        :return:
        """
        job = resource_apscheduler_setup.add_job(add_job_callback)
        resource_apscheduler_setup.remove_job(job_id=job.id)
        assert resource_apscheduler_setup.get_job(job_id=job.id) is None

    def test_scheduler_get_job(self, resource_apscheduler_setup):
        """
        Create job and then get it using job id
        :param resource_apscheduler_setup:
        :return:
        """
        job = resource_apscheduler_setup.add_job(add_job_callback)
        assert resource_apscheduler_setup.get_job(job_id=job.id) == job

    def test_scheduler_jobs_add(self, resource_apscheduler_setup):
        """
        Create and add jobs in scheduler in bulk and check if job is added one by one
        :param resource_apscheduler_setup:
        :return:
        """
        jobs = []
        for i in range(10):
            jobs.append((resource_apscheduler_setup.add_job(add_job_callback)).id)

        for job_id in jobs:
            assert resource_apscheduler_setup.get_job(job_id=job_id).id is job_id

    def test_scheduler_jobs_remove(self, resource_apscheduler_setup):
        """
        add the jobs and then remove all of them. then check if job is none
        :param resource_apscheduler_setup:
        :return:
        """
        jobs = []
        for i in range(10):
            jobs.append(resource_apscheduler_setup.add_job(add_job_callback).id)
        resource_apscheduler_setup.remove_all_jobs()

        for job_id in jobs:
            assert resource_apscheduler_setup.get_job(job_id=job_id) is None

