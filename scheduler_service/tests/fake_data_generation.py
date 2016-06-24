import json
import random
import datetime
from copy import deepcopy
import requests
from faker import Factory

from scheduler_service.common.models.user import User
from setup_environment.create_dummy_users import create_dummy_users

fake = Factory.create()

create_dummy_users()

scheduler_data = {
    "task_type": "periodic",
    "url": "https://httpbin.org/post",
    "post_data": {
        "campaign_name": "SMS Campaign",
        "phone_number": "09230862348",
        "smart_list_id": 123456,
        "content": "text to be sent as sms"
    }
}

DATA_NUM = 100
jobs_to_pause_prob = 5
job_id_list = []

bearer_tokens = ['9ery8pVOxTOvQU0oJsENRek4lj6ZT6', 'uTl6zNUdoNATwwUg0GOuSFvyrtyCCW', 'iM0WU5y76laIJph5LS1jidKcdjWk4a']
task_type_opts = ['periodic', 'one_time']
post_methods = ['get', 'post', 'patch', 'delete']

for i in range(0, DATA_NUM):
    data = deepcopy(scheduler_data)

    data['task_type'] = task_type_opts[random.randrange(1, 3) - 1]

    if data['task_type'] == 'periodic':
        data['start_datetime'] = (datetime.datetime.now() + datetime.timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        data['end_datetime'] = (datetime.datetime.now() + datetime.timedelta(days=40)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        data['frequency'] = random.randrange(3600, 5 * 24 * 3600)
    else:
        data['run_datetime'] = (datetime.datetime.now() + datetime.timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    data['url'] = 'http://www.{0}.com'.format(fake.first_name())
    data['request_method'] = post_methods[random.randrange(1, len(post_methods)) - 1]
    if data['request_method'] in ['get', 'delete']:
        del data['post_data']

    headers = {
        'Authorization': 'Bearer %s' % bearer_tokens[random.randrange(1, len(bearer_tokens) + 1) - 1],
        'Content-Type': 'application/json'
    }

    if 1 == random.randrange(1, 20):
        secret_key_id, token = User.generate_jw_token()
        headers = {'Authorization': token,
                  'X-Talent-Secret-Key-ID': secret_key_id,
                  'Content-Type': 'application/json'}
        data['task_name'] = fake.last_name()

    res = requests.post('http://localhost:8011/v1/tasks', data=json.dumps(data),
                        headers=headers)
    if res.status_code != 201:
        print res
        continue

    if 1 == random.randrange(1, jobs_to_pause_prob):
        requests.post('http://localhost:8011/v1/tasks/%s/pause' % res.json()['id'], data=json.dumps(data),
                      headers=headers)

    job_id_list.append(res.json()['id'])
