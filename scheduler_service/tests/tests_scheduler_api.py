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
    "frequency": {
        "day": 5,
        "hour": 6
    },
    "url": "http://getTalent.com/sms/send/",
    "start_time": "2015-12-05T08:00:00-05:00",
    "end_time": "2016-01-05T08:00:00-05:00",
    "post_data": {
        "campaign_name": "SMS Campaign",
        "phone_number": "09230862348",
        "smart_list_id": 123456,
        "content": "text to be sent as sms"
    }
}


@pytest.mark.usefixtures('resource_apscheduler_setup', 'auth_data')
class TestSchedulingViews:
    """
    Test Cases for scheduling, resume, stop, remove job
    """

    def test_scheduled_get_jobs(self, auth_data):
        """
        Create jobs and schedule them and then get all scheduled jobs
        :return:
        """
        # unschedule all jobs
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        jobs = []

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_get = requests.get(APP_URL + '/tasks/',
                                    headers=headers)
        assert response_get.status_code == 200
        get_jobs = json.loads(response_get.text)
        assert len(jobs) == int(get_jobs['count'])
        for ijob in get_jobs['tasks']:
            assert ijob['id'] in jobs

    def test_schedule_job(self, auth_data):
        """
        Create and schedule job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)
        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

    def test_scheduled_job_stop(self, auth_data):
        """
        Create and schedule job then stop
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)
        assert response.status_code == 201
        job_id = response.json()['id']

        # send job stop request
        response_stop = requests.get(APP_URL + '/tasks/' + job_id + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 200

        # try stopping again, it shouldn't affect job state
        response_stop_again = requests.get(APP_URL + '/tasks/' + job_id + '/pause/',
                                           headers=headers)
        assert response_stop_again.status_code == 200

    def test_scheduled_job_resume(self, auth_data):
        """
        Create and schedule job then stop and then again resume
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)
        assert response.status_code == 201
        job_id = response.json()['id']

        # send job stop request
        response_stop = requests.get(APP_URL + '/tasks/' + job_id + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 200

        # resume job stop request
        response_resume = requests.get(APP_URL + '/tasks/' + job_id + '/resume/',
                                       headers=headers)
        assert response_resume.status_code == 200

        # resume job stop request again - does not affect
        response_resume_again = requests.get(APP_URL + '/tasks/' + job_id + '/resume/',
                                             headers=headers)
        assert response_resume_again.status_code == 200

    def test_scheduled_job_unschedule(self, auth_data):
        """
        Create and schedule job then remove job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)
        assert response.status_code == 201
        job_id = response.json()['id']
        response_remove = requests.delete(APP_URL + '/tasks/' + job_id,
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_scheduled_jobs_unschedule(self, auth_data):
        """
        Create and schedule jobs then remove all jobs
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)
        jobs = []

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        # schedule some jobs
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        # response_unschedule = requests.delete(APP_URL + '/tasks/',
        #                                      data=dict(ids=jobs))
        for job_id in jobs:
            response_remove = requests.delete(APP_URL + '/tasks/' + job_id,
                                              headers=headers)
            assert response_remove.status_code == 200

    def test_scheduled_get_job(self, auth_data):
        """
        Create a job and schedule it and then get that scheduled job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)
        assert response.status_code == 201
        data = json.loads(response.text)

        response_get = requests.get(APP_URL + '/tasks/' + data['id'],
                                    headers=headers)
        assert response_get.status_code == 200
        assert json.loads(response_get.text)['task']['id'] == data['id']

    def test_scheduled_post_job_without_token(self):
        """
        Create a job and schedule it and then get that scheduled job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer invalid_token',
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)
        assert response.status_code == 401

    def test_scheduled_get_job_without_token(self, auth_data):
        """
        Create a job and schedule it and then get that scheduled job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        #set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        response_get = requests.get(APP_URL + '/tasks/' + data['id'],
                                    headers=headers)

        assert response_get.status_code == 401

    def test_scheduled_resume_job_without_token(self, auth_data):
        """
        Create a job and schedule it and then get that scheduled job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # send job stop request
        response_stop = requests.get(APP_URL + '/tasks/' + data['id'] + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 200

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        response_get = requests.get(APP_URL + '/tasks/' + data['id'] + '/resume/',
                                    headers=headers)

        assert response_get.status_code == 401

    def test_scheduled_pause_job_without_token(self, auth_data):
        """
        Create a job and schedule it and then get that scheduled job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        # send job stop request
        response_stop = requests.get(APP_URL + '/tasks/' + data['id'] + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 401

    def test_scheduled_delete_job_without_token(self, auth_data):
        """
        Create a job and schedule it and then get that scheduled job
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        # send job delete request
        response_delete = requests.delete(APP_URL + '/tasks/' + data['id'],
                                          headers=headers)
        assert response_delete.status_code == 401

        headers['Authorization'] = auth_data['access_token']

        response_delete2 = requests.delete(APP_URL + '/tasks/' + data['id'],
                                           headers=headers)

        assert response_delete2.status_code == 200

        # send job delete request...#job should n't exist now
        response_delete3 = requests.delete(APP_URL + '/tasks/' + data['id'],
                                           headers=headers)

        assert response_delete3.status_code == 404

    def test_scheduled_jobs_unschedule_without_token(self, auth_data):
        """
        Create and schedule jobs then remove all jobs
        :return:
        """
        new_job = job.copy()
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        new_job['start_date'] = str(start_date)
        new_job['end_date'] = str(end_date)
        jobs = []

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        # schedule some jobs
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(new_job),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        headers['Authorization'] = 'Bearer invalid_token'

        for job_id in jobs:
            response_remove = requests.delete(APP_URL + '/tasks/' + job_id,
                                              headers=headers)
            assert response_remove.status_code == 401

"""
Callback method which is called when job next_run_time comes
"""


def temp_job():
    print 'job added'
    pass
