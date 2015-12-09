"""
This file contains unit tests that hit scheduling service endpoints and
test schedule/resume/pause/remove with single and multiple jobs and with authorized and unauthorized token.
"""
import json
import datetime
from pytz import timezone
from time import sleep
from dateutil.parser import parse
import pytest
import requests
from conftest import APP_URL


@pytest.mark.usefixtures('auth_data', 'job_config', 'job_config_two')
class TestSchedulingViews:
    """
    Test Cases for scheduling, resume, stop, remove single or multiple jobs
    """

    def test_one_scheduled_job(self, auth_data, job_config):
        """
        Create a job by hitting the endpoint and make sure response
        is correct.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data['id'] is not None

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_stopping_scheduled_job(self, auth_data, job_config):
        """
        Create a job by hitting endpoint
        then stop it using endpoint. We then stop it again and
        it should give error (6053).
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(response.json()['id'])
        job_id = jobs[0]

        # send job stop request
        response_stop = requests.post(APP_URL + '/tasks/' + job_id + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 200

        # Paused jobs have their 'next_run_datetime' set to 'None'
        response = requests.get(APP_URL + '/tasks/id/' + job_id, headers=headers)
        next_run_datetime = response.json()['task']['next_run_datetime']
        assert next_run_datetime == 'None'

        # try stopping again, it should throw exception
        response_stop_again = requests.post(APP_URL + '/tasks/' + job_id + '/pause/',
                                           headers=headers)
        assert response_stop_again.status_code == 500 and \
              response_stop_again.json()['error']['code'] == 6053

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + job_id,
                                          headers=headers)
        assert response_remove.status_code == 200
        del jobs[:1]
        # Check if rest of the jobs are okay
        for job_id in jobs:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id,
                                        headers=headers)
            assert response_get.json()['task']['id'] == job_id and \
                   response_get.json()['task']['next_run_datetime'] is not None

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_resuming_scheduled_job(self, auth_data, job_config):
        """
        Create a job by hitting endpoint
        then schedule that job using endpoint
        then stop by endpoint
        then again resume it using endpoint.
        then check if its next_run_datetime is not None
        then delete all jobs
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(response.json()['id'])
        job_id = jobs[0]

        # send job stop request
        response_stop = requests.post(APP_URL + '/tasks/' + job_id + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 200

        # Paused jobs have their next_run_datetime set to 'None'
        response = requests.get(APP_URL + '/tasks/id/' + job_id, headers=headers)
        next_run_datetime = response.json()['task']['next_run_datetime']
        assert next_run_datetime == 'None'

        # resume job stop request
        response_resume = requests.post(APP_URL + '/tasks/' + job_id + '/resume/',
                                       headers=headers)
        assert response_resume.status_code == 200

        # Normal jobs don't have their next_run_datetime set to 'None'
        response = requests.get(APP_URL + '/tasks/id/' + job_id, headers=headers)
        next_run_datetime = response.json()['task']['next_run_datetime']
        assert next_run_datetime != 'None'

        # resume job stop request again - does not affect
        response_resume_again = requests.post(APP_URL + '/tasks/' + job_id + '/resume/',
                                             headers=headers)
        assert response_resume_again.status_code == 500 and \
               response_resume_again.json()['error']['code'] == 6054

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + job_id,
                                          headers=headers)
        assert response_remove.status_code == 200

        # delete job id which is deleted
        del jobs[:1]
        for job_id in jobs:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id,
                                        headers=headers)
            assert response_get.json()['task']['id'] == job_id and\
                   response_get.json()['task']['next_run_datetime'] is not None

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_resuming_scheduled_jobs(self, auth_data, job_config):
        """
        Create multiple jobs i.e 10 below
        then schedule all created jobs
        then pause a job
        then check if next_run_datetime is None => Paused job have next_run_datetime = None
        then again resume that single job.
        then delete all jobs
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs_id = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        # send job stop request
        response_stop = requests.post(APP_URL + '/tasks/pause/', data=json.dumps(dict(ids=jobs_id)),
                                     headers=headers)
        assert response_stop.status_code == 200

        response_resume = requests.post(APP_URL + '/tasks/resume/', data=json.dumps(dict(ids=jobs_id)),
                                       headers=headers)

        assert response_resume.status_code == 200

        jobs = []
        # Paused jobs have their next_run_datetime set to 'None'
        for job_id in jobs_id:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id,
                                        headers=headers)
            jobs.append(response_get.json()['task'])

        for res in jobs:
            next_run_datetime = res['next_run_datetime']
            assert next_run_datetime is not 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_stopping_scheduled_jobs(self, auth_data, job_config):
        """
        Create jobs using endpoint
        then schedule jobs
        then stop a job
        then check for next_run_datetime, next_run_datetime is None for stopped job
        then delete all.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs_id = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        # send job stop request
        response_stop = requests.post(APP_URL + '/tasks/pause/', data=json.dumps(dict(ids=jobs_id)),
                                     headers=headers)
        assert response_stop.status_code == 200

        jobs = []
        # Paused jobs have their next_run_datetime set to 'None'
        for job_id in jobs_id:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id, data=json.dumps(dict(ids=jobs_id)),
                                        headers=headers)
            jobs.append(response_get.json()['task'])
        for res in jobs:
            next_run_datetime = res['next_run_datetime']
            assert next_run_datetime == 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_job_scheduling_and_removal(self, auth_data, job_config):
        """
        Create a job using endpoint
        then schedule job
        then remove it.
        then try to get job, it should give 404 status code
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)
        assert response.status_code == 201
        job_id = response.json()['id']
        response_remove = requests.delete(APP_URL + '/tasks/id/' + job_id,
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + job_id, headers=headers)
        assert response.status_code == 404

    def test_get_multiple_scheduled_jobs(self, auth_data, job_config):
        """
        Create a job
        then schedule job
        then stop job
        then again resume it.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs_id = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        # Paused jobs have their next_run_datetime set to 'None'
        response_get = requests.get(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                    headers=headers)

        get_jobs_id = map(lambda job_: job_['id'], response_get.json()['tasks'])
        for job in jobs_id:
            assert job in get_jobs_id
        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_multiple_job_scheduling_and_removal(self, auth_data, job_config):
        """
        Create multiple jobs
        then schedule jobs
        then remove all jobs
         Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        jobs = []

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        # schedule some jobs and remove all of them
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_remove_jobs = requests.delete(APP_URL + '/tasks/',
                                               data=json.dumps(dict(ids=jobs)),
                                               headers=headers)

        assert response_remove_jobs.status_code == 200

        # add a non-existing job and check if it shows 207 status code
        del jobs[:]
        jobs.append('Non-existing job')
        # schedule some jobs and remove all of them
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_remove_jobs2 = requests.delete(APP_URL + '/tasks/',
                                                data=json.dumps(dict(ids=jobs)),
                                                headers=headers)

        assert response_remove_jobs2.status_code == 207

    def test_scheduled_get_job(self, auth_data, job_config):
        """
        Create a job using endpoint
        then schedule it
        then get that scheduled job
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)
        assert response.status_code == 201
        data = json.loads(response.text)

        response_get = requests.get(APP_URL + '/tasks/id/' + data['id'],
                                    headers=headers)
        assert response_get.status_code == 200
        assert json.loads(response_get.text)['task']['id'] == data['id']

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'], headers=headers)
        assert response.status_code == 404

    def test_schedule_job_creation_without_token(self, job_config):
        """
        Create a job without a token, it shouldn't be created and we should get a
        401 when endpoint hit
        Args:
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer invalid_token',
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)
        assert response.status_code == 401

    def test_scheduled_job_retrieval_without_token(self, auth_data, job_config):
        """
        Create a job using endpoint
        then schedule it
        then get that scheduled job without token
        and it should result in a 401.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        response_get = requests.get(APP_URL + '/tasks/id/' + data['id'],
                                    headers=headers)

        assert response_get.status_code == 401
        # Let's delete jobs now
        headers['Authorization'] = 'Bearer ' + auth_data['access_token']
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'], headers=headers)
        assert response.status_code == 404

    def test_resuming_scheduled_job_without_token(self, auth_data, job_config):
        """
        Create a job, schedule it. Then we stop it. After that we use an invalid
        token and try to resume it only to get a 401.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # send job stop request
        response_stop = requests.post(APP_URL + '/tasks/' + data['id'] + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 200

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        response_get = requests.post(APP_URL + '/tasks/' + data['id'] + '/resume/',
                                    headers=headers)

        assert response_get.status_code == 401

        # Let's delete jobs now
        headers['Authorization'] = 'Bearer ' + auth_data['access_token']
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'] , headers=headers)
        assert response.status_code == 404

    def test_pausing_scheduled_job_without_token(self, auth_data, job_config):
        """
        Create a job, and then try to pause it with an invalid token only to get a
        401.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        # send job stop request
        response_stop = requests.post(APP_URL + '/tasks/' + data['id'] + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 401

        # Let's delete jobs now
        headers['Authorization'] = 'Bearer ' + auth_data['access_token']
        response_remove = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/id/' + data['id'], headers=headers)
        assert response.status_code == 404

    def test_deleting_scheduled_job_without_token(self, auth_data, job_config):
        """
        Create a job and then try to delete the job with invalid token and
        we assert for a 401. Then we delete it with correct token and it's deleted.
        Finally, we make sure we cannot delete the job because it doesn't exist
        anymore.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        # send job delete request
        response_delete = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                          headers=headers)
        assert response_delete.status_code == 401

        headers['Authorization'] = 'Bearer ' + auth_data['access_token']

        response_delete2 = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                           headers=headers)

        assert response_delete2.status_code == 200

        # send job delete request...#job should n't exist now
        response_delete3 = requests.delete(APP_URL + '/tasks/id/' + data['id'],
                                           headers=headers)

        assert response_delete3.status_code == 404

    def test_deleting_multiple_scheduled_jobs_without_token(self, auth_data, job_config):
        """
        Create 10 jobs and then try to delete them without token and we get 401s.
        Create and schedule jobs then remove all jobs
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        jobs = []

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        # schedule some jobs
        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        headers['Authorization'] = 'Bearer invalid_token'

        for job_id in jobs:
            response_remove = requests.delete(APP_URL + '/tasks/id/' + job_id,
                                              headers=headers)
            assert response_remove.status_code == 401

        headers['Authorization'] = 'Bearer ' + auth_data['access_token']

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_resuming_scheduled_jobs_without_token(self, auth_data, job_config):
        """
        Create a job
        then schedule job
        then stop job
        then again resume job.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs_id = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        # send job stop request
        response_stop = requests.post(APP_URL + '/tasks/pause/', data=json.dumps(dict(ids=jobs_id)),
                                     headers=headers)
        assert response_stop.status_code == 200

        headers['Authorization'] = 'Bearer invalid_token'

        response_resume = requests.post(APP_URL + '/tasks/resume/', data=json.dumps(dict(ids=jobs_id)),
                                       headers=headers)

        assert response_resume.status_code == 401

        headers['Authorization'] = 'Bearer ' + auth_data['access_token']

        jobs = []
        # Resume jobs have their next_run_datetime set to next time
        for job_id in jobs_id:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id, data=json.dumps(dict(ids=jobs_id)),
                                        headers=headers)
            jobs.append(response_get.json())
        for res in jobs:
            next_run_datetime = res['task']['next_run_datetime']
            assert next_run_datetime == 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_stopping_scheduled_jobs_without_token(self, auth_data, job_config):
        """
        Create a job
        then schedule job
        then stop job
        then again resume it.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs_id = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs_id.append(response.json()['id'])

        headers['Authorization'] = 'Bearer invalid_token'

        # send job stop request
        response_stop = requests.post(APP_URL + '/tasks/pause/', data=json.dumps(dict(ids=jobs_id)),
                                     headers=headers)
        assert response_stop.status_code == 401

        headers['Authorization'] = 'Bearer ' + auth_data['access_token']
        # Paused jobs have their next_run_datetime set to 'None'
        jobs = []
        for job_id in jobs_id:
            response_get = requests.get(APP_URL + '/tasks/id/' + job_id, data=json.dumps(dict(ids=jobs_id)),
                                        headers=headers)
            jobs.append(response_get.json())
        for res in jobs:
            next_run_datetime = res['task']['next_run_datetime']
            assert next_run_datetime != 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs_id)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_check_scheduled_job_running(self, auth_data, job_config):
        """
            Create a job
            then schedule that job
            then check runtime after its frequency time and see next_run_datetime changed
            then remove it.
            Args:
                auth_data: Fixture that contains token.
                job_config (dict): Fixture that contains job config to be used as
                POST data while hitting the endpoint.
            :return:
            """
        frequency = 10
        start_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=3)
        end_date = start_date + datetime.timedelta(seconds=30)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        job_config['frequency'] = {"seconds": frequency}

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)

        assert response.status_code == 201

        # wait for 3 seconds for the job to start
        sleep(3)
        old_run_time = job_config['start_datetime']

        # wait for the next runtime and then check if runtime changed and is greater
        for x in range(2):
            sleep(frequency)
            response_running = requests.get(APP_URL + '/tasks/id/' + response.json()['id'],
                                            headers=headers)
            task = response_running.json()

            # parse date into UTC format
            str_current_run = parse(old_run_time)
            current_run = str_current_run.replace(tzinfo=timezone('UTC'))
            str_next_run = parse(task['task']['next_run_datetime'])
            next_run = str_next_run.replace(tzinfo=timezone('UTC'))

            # current run time should be lower than next run time to ensure job is running in interval
            assert current_run < next_run

            # set the old_run_time to the next_run_datetime
            old_run_time = task['task']['next_run_datetime']

        # delete job
        response_delete = requests.delete(APP_URL + '/tasks/id/' + response.json()['id'],
                                          headers=headers)

        assert response_delete.status_code == 200

    def test_bulk_job_scheduling_and_removal_load_testing(self, auth_data, job_config):
        """
        Create multiple jobs in bulk for load testing
        then schedule jobs
        then remove all jobs
         Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(days=2)
        job_config['start_datetime'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_datetime'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs = []

        # check with 10,000 jobs
        load_number = 10000
        # schedule some jobs and remove all of them
        for i in range(load_number):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        chunk_size = 100

        # delete all created jobs
        for i in range(0, load_number, chunk_size):
            jobs_chunk = jobs[i:i + chunk_size]
            response_remove_jobs = requests.delete(APP_URL + '/tasks/',
                                                   data=json.dumps(dict(ids=jobs_chunk)),
                                                   headers=headers)

            assert response_remove_jobs.status_code == 200

