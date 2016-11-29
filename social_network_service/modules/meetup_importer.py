"""
This module and containing function is to run as a lambda function
"""
import os
import json
import time
import boto3
from datetime import datetime, timedelta
import requests
import pymysql
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

db = os.environ['db']
host = os.environ['host']
user = os.environ['user']
password = os.environ['password']
importer_type = os.environ['type']
interval = os.environ.get('interval', 4)
stream_url = os.environ['stream_url']
webhook_url = os.environ['webhook_url']
environment = os.environ.get('environment', 'staging')

# Connect to the database


lambda_client = boto3.client('lambda')


def meetup_importer(event, context):
    """
    This lambda function is invoked first time and then it keeps up running by invoking itself every 4 minutes.
    There is a limit of 5 minutes of execution on any lambda function so this function can't run infinitely
    without recursively calling itself. It invokes itself using lambda API.
    """
    start = datetime.utcnow()
    logger.info('Meetup importer started at UTC: %s' % datetime.utcnow())
    logger.info('Meetup importer URL: %s' % stream_url)
    connection = pymysql.connect(host=host, user=user, password=password, db=db,
                                 cursorclass=pymysql.cursors.DictCursor, autocommit=True)
    while True:
        try:
            response = requests.get(stream_url, stream=True, timeout=30)
            logger.info('Meetup Stream Response Status: %s' % response.status_code)
            for raw_data in response.iter_lines():
                if raw_data:
                    try:
                        data = json.loads(raw_data)
                        if importer_type == 'event':
                            group_id = data['group']['id']
                        else:
                            group_id = data['group']['group_id']

                        sql = "SELECT `id` from `meetup_group` where `group_id` = %s"
                        cursor = connection.cursor()
                        cursor.execute(sql, (group_id,))
                        result = cursor.fetchone()
                        cursor.close()
                        if result:
                            logger.info('Going to save %s: %s' % (importer_type, data))
                            data = {
                                'type': importer_type,
                                importer_type: data
                            }
                            response = requests.post(webhook_url, data=json.dumps(data),
                                                     headers={'Content-Type': 'application/json'})
                            logger.info(response.text)
                    except ValueError:
                        pass
                    except Exception as e:
                        logger.exception('Error occurred while parsing event data, Error: %s' % e)
                        connection.rollback()
                        break

                if (datetime.utcnow() - start) > timedelta(minutes=int(interval)):
                    logger.info('Breaking outer loop after %s minutes at: %s' % (interval, datetime.utcnow()))
                    lambda_client.invoke(
                        FunctionName=context.function_name,
                        InvocationType='Event',
                        LogType='None',
                        Payload='{"key": "start again"}'
                    )
                    connection.close()
                    return 'Start Again'
        except Exception as e:
            logger.error('Out of main loop. Cause: %s' % e)
            time.sleep(10)

if __name__ == "__main__":
    meetup_importer(None, None)
