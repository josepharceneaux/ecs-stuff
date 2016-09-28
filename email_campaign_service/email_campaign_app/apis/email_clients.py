"""
 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains API endpoints for
    1) Adding server-side-email-clients so that users can send email-campaigns with their desired servers
    2) Retrieving email-conversations of users

    Following is a list of API endpoints:

        - EmailClients: /v1/email-clients

            POST    : Adds new server-side-email-client in database table email_client_credentials

        - EmailConversations: /v1/email-conversations

            POST     : Retrieves email-conversation of all the getTalent users

"""
# Standard Library
import json
import types
from base64 import b64encode
from datetime import datetime, timedelta

# Third Party
import requests
from simplecrypt import encrypt
from flask_restful import Resource
from flask import request, Blueprint

# Service Specific
from email_campaign_service.common.models.user import User
from email_campaign_service.email_campaign_app import logger, app
from email_campaign_service.common.utils.datetime_utils import DatetimeUtils
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.json_schema.email_clients import EMAIL_CLIENTS_SCHEMA
from email_campaign_service.common.utils.validators import get_json_data_if_validated
from email_campaign_service.common.models.email_campaign import EmailClientCredentials
from email_campaign_service.modules.utils import (TASK_ALREADY_SCHEDULED, import_email_conversations)
from email_campaign_service.modules.utils import (EmailClientBase, format_email_client_data)
from email_campaign_service.common.error_handling import (InvalidUsage, InternalServerError)

# Common utils
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.utils.api_utils import api_route
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.routes import (EmailCampaignApi, EmailCampaignApiUrl, SchedulerApiUrl)

# Blueprint for email-clients API
email_clients_blueprint = Blueprint('email_clients_api', __name__)
api = TalentApi()
api.init_app(email_clients_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(EmailCampaignApi.CLIENTS)
class EmailClientsEndpoint(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    def post(self):
        """
        This will save an entry in database table email_client_credentials.

        .. Request Body::
                        {
                            "host": "Host Name",
                            "port": 123,
                            "name": "Server Name",
                            "email": "test.gettalent@gmail.com",
                            "password": "password",
                        }

        .. Response::
                       {
                          "id": 347
                       }

        .. Status:: 201 (Resource created)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    500 (Internal server error)
        """
        data = get_json_data_if_validated(request, EMAIL_CLIENTS_SCHEMA)
        data = format_email_client_data(data)
        data['user_id'] = request.user.id
        client_in_db = EmailClientCredentials.get_by_user_id_host_and_email(data['user_id'],
                                                                            data['host'], data['email'])
        if client_in_db:
            raise InvalidUsage('Email client with given data already present in database')

        client = EmailClientBase.get_client(data['host'])
        client = client(data['host'], data['port'], data['email'], data['password'])
        client.connect()
        client.authenticate()
        # Encrypt password
        ciphered_password = encrypt(app.config[TalentConfigKeys.ENCRYPTION_KEY], data['password'])
        b64_password = b64encode(ciphered_password)
        data['password'] = b64_password
        email_client = EmailClientCredentials(**data)
        EmailClientCredentials.save(email_client)
        return {'id': email_client.id}, requests.codes.CREATED

    def get(self):
        """
        This will get all the email-clients added by requested user from email_client_credentials.

        .. Response::

            { 'email_client_credentials:
                    [
                            {
                                "id": 1,
                                "user_id": 12345
                                "host": "server_name",
                                "port": 123,
                                "name": "Server Name 1",
                                "email": "test.gettalent@gmail.com",
                                "password": "password_1",
                                "updated_datetime": "2016-09-26 14:20:06"
                            },
                            {
                                "id": 2,
                                "user_id": 12345
                                "host": "server_name",
                                "port": 123,
                                "name": "Server Name 2",
                                "email": "test.gettalent@gmail.com",
                                "password": "password_2",
                                "updated_datetime": "2016-09-26 14:20:06"
                            }
                    ]
            }

        .. Status:: 200 (Resource created)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    500 (Internal server error)
        """
        server_type = request.args.get('type', 'outgoing')
        email_client_credentials = [email_client_credential.to_json() for email_client_credential in
                                    EmailClientCredentials.get_by_user_id_and_filter_by_name(request.user.id,
                                                                                             server_type)]
        return {'email_client_credentials': email_client_credentials}, requests.codes.OK


@api.route(EmailCampaignApi.CONVERSATIONS)
class EmailConversations(Resource):

    # Access token decorator
    decorators = [require_oauth(allow_null_user=True)]

    def post(self):
        """
        This endpoint will be hit by scheduler-service. It will loop over the entries in database table
        email_client_credentials for which server-type is "incoming" and will save the details of email-conversation
        in database table email-conversations.

        .. Status:: 401 (Unauthorized to access getTalent)
                    500 (Internal server error)
        """
        email_clients = EmailClientCredentials.get_by_type(EmailClientCredentials.CLIENT_TYPES['incoming'])
        for email_client in email_clients:
            import_email_conversations(email_client)


def schedule_job_for_email_conversations():
    """
    Schedule general job that hits /v1/email-conversations endpoint every hour.
    """
    url = EmailCampaignApiUrl.CONVERSATIONS
    task_name = 'get_email_conversations'
    start_datetime = datetime.utcnow() + timedelta(seconds=15)
    # Schedule for next 100 years
    end_datetime = datetime.utcnow() + timedelta(weeks=52 * 100)
    frequency = 3600

    secret_key_id, access_token = User.generate_jw_token()
    headers = {
        'X-Talent-Secret-Key-ID': secret_key_id,
        'Authorization': access_token
    }
    data = {
        'start_datetime': start_datetime.strftime(DatetimeUtils.ISO8601_FORMAT),
        'end_datetime': end_datetime.strftime(DatetimeUtils.ISO8601_FORMAT),
        'frequency': frequency,
        'is_jwt_request': True
    }

    logger.info('Checking if `{}` task already running...'.format(task_name))
    response = requests.get(SchedulerApiUrl.TASK_NAME % task_name, headers=headers)
    # If job is not scheduled then schedule it
    if response.status_code == requests.codes.not_found:
        logger.info('Task {} not scheduled. Scheduling {} task.'.format(task_name, task_name))
        data.update({'url': url})
        data.update({'task_name': task_name, 'task_type': 'periodic'})

        response = requests.post(SchedulerApiUrl.TASKS, headers=headers, data=json.dumps(data))
        is_already_created = response.status_code == requests.codes.created \
                             or response.json()['error']['code'] == TASK_ALREADY_SCHEDULED
        if not is_already_created:
            logger.error(response.text)
            raise InternalServerError(error_message='Unable to schedule job for getting email-conversations')
    elif response.status_code == requests.codes.ok:
        logger.info('Job already scheduled. {}'.format(response.text))
    else:
        logger.error(response.text)
