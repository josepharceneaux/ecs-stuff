import json
import datetime
import pytest
import requests

__author__ = 'saad'

APP_URL = 'http://localhost:8009'


"""
Job dictionary object for testing
"""

job = {
    'func': 'scheduler_views_tests:temp_job',
    'trigger': 'interval',
    'seconds': 10
}


@pytest.mark.usefixtures('resource_apscheduler_setup')
class TestSchedulingViews:
    """
    Test Cases for scheduling, resume, stop, remove job
    """
    def test_schedule_job(self):
        """
        Create and schedule job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = (str(start_date)).split('.')[0]
        new_job['end_date'] = (str(end_date)).split('.')[0]
        response = requests.post(APP_URL + '/schedule/', data=json.dumps(new_job))
        assert response.status_code == 200
        data = json.loads(response.text)
        assert data['id'] is not None

    def test_scheduled_job_stop(self):
        """
        Create and schedule job then stop
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = (str(start_date)).split('.')[0]
        new_job['end_date'] = (str(end_date)).split('.')[0]
        response = requests.post(APP_URL + '/schedule/', data=json.dumps(new_job))
        assert response.status_code == 200
        job_id = response.json()['id']

        #send job stop request
        response_stop = requests.post(APP_URL + '/stop/' + job_id)
        assert response_stop.status_code == 200

    def test_scheduled_job_resume(self):
        """
        Create and schedule job then stop and then again resume
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = (str(start_date)).split('.')[0]
        new_job['end_date'] = (str(end_date)).split('.')[0]
        response = requests.post(APP_URL + '/schedule/', data=json.dumps(new_job))
        assert response.status_code == 200
        job_id = response.json()['id']

        # send job stop request
        response_stop = requests.post(APP_URL + '/stop/' + job_id)
        assert response_stop.status_code == 200

        # resume job stop request
        response_resume = requests.post(APP_URL + '/resume/' + job_id)
        assert response_resume.status_code == 200

    def test_scheduled_job_unschedule(self):
        """
        Create and schedule job then remove job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = (str(start_date)).split('.')[0]
        new_job['end_date'] = (str(end_date)).split('.')[0]
        response = requests.post(APP_URL + '/schedule/', data=json.dumps(new_job))
        assert response.status_code == 200
        job_id = response.json()['id']
        response_remove = requests.post(APP_URL + '/unschedule/' + job_id)
        assert response_remove.status_code == 200

    def test_scheduled_jobs_unschedule(self):
        """
        Create and schedule jobs then remove all jobs
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = (str(start_date)).split('.')[0]
        new_job['end_date'] = (str(end_date)).split('.')[0]
        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/schedule/', data=json.dumps(new_job))
            assert response.status_code == 200
            jobs.append(json.loads(response.text)['id'])

        response_unschedule = requests.post(APP_URL + '/unschedule-jobs/')
        assert response_unschedule.status_code == 200

        #check if there is any job left
        response_check_empty = requests.get(APP_URL + '/get-jobs/')
        data = json.loads(response_check_empty.text)
        assert len(data) == 0

    def test_scheduled_get_job(self):
        """
        Create a job and schedule it and then get that scheduled job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = (str(start_date)).split('.')[0]
        new_job['end_date'] = (str(end_date)).split('.')[0]
        response = requests.post(APP_URL + '/schedule/', data=json.dumps(new_job))
        assert response.status_code == 200
        data = json.loads(response.text)

        response_get = requests.get(APP_URL + '/get-job/' + data['id'])
        assert response_get.status_code == 200
        assert json.loads(response_get.text)['id'] == data['id']

    def test_scheduled_get_jobs(self):
        """
        Create jobs and schedule them and then get all scheduled jobs
        :return:
        """
        #unschedule all jobs
        response_unschedule = requests.post(APP_URL + '/unschedule-jobs/')
        assert response_unschedule.status_code == 200

        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = (str(start_date)).split('.')[0]
        new_job['end_date'] = (str(end_date)).split('.')[0]

        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/schedule/', data=json.dumps(new_job))
            assert response.status_code == 200
            jobs.append(json.loads(response.text)['id'])

        response_get = requests.get(APP_URL + '/get-jobs/')
        assert response_get.status_code == 200
        get_jobs = json.loads(response_get.text)
        assert len(jobs) == len(get_jobs)
        for ijob in get_jobs:
            assert ijob['id'] in jobs


"""
Callback method which is called when job next_run_time comes
"""


def temp_job():
    print 'job added'
    pass
