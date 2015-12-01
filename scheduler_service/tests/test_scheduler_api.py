"""
This file contains unit tests that hit scheduling service endpoints and
test schedule/resume/pause/remove jobs.
"""
import json
import datetime
import pytest
import requests
from conftest import APP_URL


@pytest.mark.usefixtures('auth_data', 'job_config')
class TestSchedulingViews:
    """
    Test Cases for scheduling, resume, stop, remove job
    """

    def test_multiple_scheduled_jobs(self, auth_data, job_config):
        """
        Create 10 jobs by hitting the endpoint. Once jobs are created then we
        retrieve them and finally make sure the count is same.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        jobs = []

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(json.loads(response.text)['id'])

        response_get = requests.get(APP_URL + '/tasks/',
                                    headers=headers)

        assert response_get.status_code == 200
        get_jobs = response_get.json()
        assert len(jobs) == int(get_jobs['count'])

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

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
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)
        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_stopping_scheduled_job(self, auth_data, job_config):
        """
        Create a job and then stop it. We then stop it again and
        it doesn't effect.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

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
        response_stop = requests.get(APP_URL + '/tasks/' + job_id + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 200

        # Paused jobs have their 'next_run_time' set to 'None'
        response = requests.get(APP_URL + '/tasks/' + job_id, headers=headers)
        next_run_time = response.json()['task']['next_run_time']
        assert next_run_time == 'None'

        # try stopping again, it should throw exception
        response_stop_again = requests.get(APP_URL + '/tasks/' + job_id + '/pause/',
                                           headers=headers)
        assert response_stop_again.status_code == 200 and response_stop_again.json()['code'] == 6053

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/' + job_id,
                                          headers=headers)
        assert response_remove.status_code == 200
        del jobs[:1]
        # Check if rest of the jobs are okay
        for job_id in jobs:
            response_get = requests.get(APP_URL + '/tasks/' + job_id,
                                        headers=headers)
            assert response_get.json()['task']['id'] == job_id and \
                   response_get.json()['task']['next_run_time'] is not None

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_resuming_scheduled_job(self, auth_data, job_config):
        """
        Create and schedule job then stop and then again resume it.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

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
        response_stop = requests.get(APP_URL + '/tasks/' + job_id + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 200

        # Paused jobs have their next_run_time set to 'None'
        response = requests.get(APP_URL + '/tasks/' + job_id, headers=headers)
        next_run_time = response.json()['task']['next_run_time']
        assert next_run_time == 'None'

        # resume job stop request
        response_resume = requests.get(APP_URL + '/tasks/' + job_id + '/resume/',
                                       headers=headers)
        assert response_resume.status_code == 200

        # Normal jobs don't have their next_run_time set to 'None'
        response = requests.get(APP_URL + '/tasks/', headers=headers)
        next_run_time = response.json()['tasks'][0]['next_run_time']
        assert next_run_time != 'None'

        # resume job stop request again - does not affect
        response_resume_again = requests.get(APP_URL + '/tasks/' + job_id + '/resume/',
                                             headers=headers)
        assert response_resume_again.status_code == 200 and response_resume_again.json()['code'] == 6054

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/' + job_id,
                                          headers=headers)
        assert response_remove.status_code == 200

        # delete job id which is deleted
        del jobs[:1]
        for job_id in jobs:
            response_get = requests.get(APP_URL + '/tasks/' + job_id,
                                        headers=headers)
            assert response_get.json()['task']['id'] == job_id and\
                   response_get.json()['task']['next_run_time'] is not None

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_resuming_scheduled_jobs(self, auth_data, job_config):
        """
        Create and schedule job then stop and then again resume it.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        # send job stop request
        response_stop = requests.get(APP_URL + '/tasks-pause/', data=json.dumps(dict(ids=jobs)),
                                     headers=headers)
        assert response_stop.status_code == 200

        response_resume = requests.get(APP_URL + '/tasks-resume/', data=json.dumps(dict(ids=jobs)),
                                       headers=headers)

        assert response_resume.status_code == 200

        # Paused jobs have their next_run_time set to 'None'
        response_get = requests.get(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                    headers=headers)
        for res in response_get.json()['tasks']:
            next_run_time = res['next_run_time']
            assert next_run_time is not 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_stopping_scheduled_jobs(self, auth_data, job_config):
        """
        Create and schedule job then stop and then again resume it.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        # send job stop request
        response_stop = requests.get(APP_URL + '/tasks-pause/', data=json.dumps(dict(ids=jobs)),
                                     headers=headers)
        assert response_stop.status_code == 200

        response_resume = requests.get(APP_URL + '/tasks-pause/', data=json.dumps(dict(ids=jobs)),
                                       headers=headers)

        assert response_resume.status_code == 200

        # Paused jobs have their next_run_time set to 'None'
        response_get = requests.get(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                    headers=headers)
        for res in response_get.json()['tasks']:
            next_run_time = res['next_run_time']
            assert next_run_time == 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_job_scheduling_and_removal(self, auth_data, job_config):
        """
        Create and schedule job then remove it.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)
        assert response.status_code == 201
        job_id = response.json()['id']
        response_remove = requests.delete(APP_URL + '/tasks/' + job_id,
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/', headers=headers)
        tasks = response.json()['tasks']
        assert len(tasks) == 0

    def test_multiple_job_scheduling_and_removal(self, auth_data, job_config):
        """
        Create and schedule jobs then remove all jobs
         Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
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
        Create a job and schedule it and then get that scheduled job
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)
        assert response.status_code == 201
        data = json.loads(response.text)

        response_get = requests.get(APP_URL + '/tasks/' + data['id'],
                                    headers=headers)
        assert response_get.status_code == 200
        assert json.loads(response_get.text)['task']['id'] == data['id']

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/', headers=headers)
        tasks = response.json()['tasks']
        assert len(tasks) == 0

    def test_schedule_job_creation_without_token(self, job_config):
        """
        Create a job without a token, it shouldn't be created and we should get a
        401.
        Args:
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer invalid_token',
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)
        assert response.status_code == 401

    def test_scheduled_job_retrieval_without_token(self, auth_data, job_config):
        """
        Create a job and schedule it and then get that scheduled job without token
        and it should result in a 401.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                 headers=headers)

        assert response.status_code == 201
        data = json.loads(response.text)
        assert data['id'] is not None

        # set the token to invalid
        headers['Authorization'] = 'Bearer invalid_token'

        response_get = requests.get(APP_URL + '/tasks/' + data['id'],
                                    headers=headers)

        assert response_get.status_code == 401
        # Let's delete jobs now
        headers['Authorization'] = auth_data['access_token']
        response_remove = requests.delete(APP_URL + '/tasks/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/', headers=headers)
        tasks = response.json()['tasks']
        assert len(tasks) == 0

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
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
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

        # Let's delete jobs now
        headers['Authorization'] = auth_data['access_token']
        response_remove = requests.delete(APP_URL + '/tasks/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/', headers=headers)
        tasks = response.json()['tasks']
        assert len(tasks) == 0

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
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

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
        response_stop = requests.get(APP_URL + '/tasks/' + data['id'] + '/pause/',
                                     headers=headers)
        assert response_stop.status_code == 401

        # Let's delete jobs now
        headers['Authorization'] = auth_data['access_token']
        response_remove = requests.delete(APP_URL + '/tasks/' + data['id'],
                                          headers=headers)
        assert response_remove.status_code == 200

        # There shouldn't be any more jobs now
        response = requests.get(APP_URL + '/tasks/', headers=headers)
        tasks = response.json()['tasks']
        assert len(tasks) == 0

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
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

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

    def test_deleting_multiple_scheduled_jobs_without_token(self, auth_data, job_config):
        """
        Create 10 jobs an dthen try to delete them without token and we get 401s.
        Create and schedule jobs then remove all jobs
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
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
            response_remove = requests.delete(APP_URL + '/tasks/' + job_id,
                                              headers=headers)
            assert response_remove.status_code == 401

        headers['Authorization'] = auth_data['access_token']

        # Let's delete jobs now
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_resuming_scheduled_jobs_without_token(self, auth_data, job_config):
        """
        Create and schedule job then stop and then again resume it.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        # send job stop request
        response_stop = requests.get(APP_URL + '/tasks-pause/', data=json.dumps(dict(ids=jobs)),
                                     headers=headers)
        assert response_stop.status_code == 200

        headers['Authorization'] = 'Bearer invalid_token'

        response_resume = requests.get(APP_URL + '/tasks-resume/', data=json.dumps(dict(ids=jobs)),
                                       headers=headers)

        assert response_resume.status_code == 401

        headers['Authorization'] = auth_data['access_token']

        # Resume jobs have their next_run_time set to next time
        response_get = requests.get(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                    headers=headers)
        for res in response_get.json()['tasks']:
            next_run_time = res['next_run_time']
            assert next_run_time == 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200

    def test_stopping_scheduled_jobs_without_token(self, auth_data, job_config):
        """
        Create and schedule job then stop and then again resume it.
        Args:
            auth_data: Fixture that contains token.
            job_config (dict): Fixture that contains job config to be used as
            POST data while hitting the endpoint.
        :return:
        """
        start_date = datetime.datetime.now() + datetime.timedelta(seconds=15)
        end_date = start_date + datetime.timedelta(hours=2)
        job_config['start_date'] = datetime.datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        job_config['end_date'] = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')

        headers = {'Authorization': 'Bearer ' + auth_data['access_token'],
                   'Content-Type': 'application/json'}

        jobs = []

        for i in range(10):
            response = requests.post(APP_URL + '/tasks/', data=json.dumps(job_config),
                                     headers=headers)
            assert response.status_code == 201
            jobs.append(response.json()['id'])

        headers['Authorization'] = 'Bearer invalid_token'

        # send job stop request
        response_stop = requests.get(APP_URL + '/tasks-pause/', data=json.dumps(dict(ids=jobs)),
                                     headers=headers)
        assert response_stop.status_code == 401

        headers['Authorization'] = auth_data['access_token']
        # Paused jobs have their next_run_time set to 'None'
        response_get = requests.get(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                    headers=headers)
        for res in response_get.json()['tasks']:
            next_run_time = res['next_run_time']
            assert next_run_time != 'None'

        # Delete all jobs
        response_remove = requests.delete(APP_URL + '/tasks/', data=json.dumps(dict(ids=jobs)),
                                          headers=headers)
        assert response_remove.status_code == 200
