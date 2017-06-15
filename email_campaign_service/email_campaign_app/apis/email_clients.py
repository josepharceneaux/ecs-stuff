"""
 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains API endpoints for
    1) Adding server-side-email-clients so that users can send email-campaigns with their desired servers
    2) Retrieving email-conversations of users

    Following is a list of API endpoints:

        - EmailClients: /v1/email-clients

            POST    : Adds new server-side-email-client in database table email_client_credentials
            GET    : GET email-client-credentials for requested user

        - EmailClientsWithId: /v1/email-clients/:id

            GET    : GET email-client-credentials for requested Id

        - EmailConversations: /v1/email-conversations

            POST     : Retrieves email-conversation of all the getTalent users
            GET     :  Returns email-conversation for requested user

"""
# Standard Library
import json
import types
from base64 import b64encode
from datetime import datetime, timedelta

# Third Party
import requests
from requests import codes
from simplecrypt import encrypt
from flask_restful import Resource
from flask import request, Blueprint

# Service Specific
from email_campaign_service.email_campaign_app import logger, app
from email_campaign_service.json_schema.email_clients import EMAIL_CLIENTS_SCHEMA
from email_campaign_service.modules.utils import (TASK_ALREADY_SCHEDULED, format_email_client_data)
from email_campaign_service.modules.email_clients import (EmailClientBase, import_email_conversations)

# Common utils
from email_campaign_service.common.models.user import User
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.utils.datetime_utils import DatetimeUtils
from email_campaign_service.common.utils.api_utils import api_route, ApiResponse
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.utils.validators import get_json_data_if_validated
from email_campaign_service.common.models.email_campaign import EmailClientCredentials, EmailCampaign
from email_campaign_service.common.routes import (EmailCampaignApi, EmailCampaignApiUrl, SchedulerApiUrl)
from email_campaign_service.common.error_handling import (InvalidUsage, InternalServerError, ResourceNotFound,
                                                          ForbiddenError)
from email_campaign_service.common.campaign_services.validators import raise_if_dict_values_are_not_int_or_long
from email_campaign_service.common.custom_errors.campaign import (EMAIL_CLIENT_NOT_FOUND, EMAIL_CLIENT_FORBIDDEN)

# Blueprint for email-clients API
email_clients_blueprint = Blueprint('email_clients_api', __name__)
api = TalentApi()
api.init_app(email_clients_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(EmailCampaignApi.EMAIL_CLIENTS)
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
        logger.info('Connecting with given email-client')
        client.connect()
        client.authenticate()
        logger.info('Successfully connected and authenticated with given email-client')
        # Encrypt password
        ciphered_password = encrypt(app.config[TalentConfigKeys.ENCRYPTION_KEY], data['password'])
        b64_password = b64encode(ciphered_password)
        data['password'] = b64_password
        email_client = EmailClientCredentials(**data)
        EmailClientCredentials.save(email_client)
        headers = {'Location': EmailCampaignApiUrl.EMAIL_CLIENT_WITH_ID % email_client.id}
        return ApiResponse(dict(id=email_client.id), status=requests.codes.CREATED, headers=headers)

    def get(self):
        """
        This will get all the email-clients added by requested user from email_client_credentials.

        .. Response::

            {
                "email_client_credentials":
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

        .. Status:: 200 (OK Response)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    500 (Internal server error)
        """
        # TODO: Return all in user's domain
        server_type = request.args.get('type', 'outgoing')
        email_client_credentials = [email_client_credential.to_json() for email_client_credential in
                                    EmailClientCredentials.get_by_user_id_and_filter_by_name(request.user.id,
                                                                                             server_type)]
        return {'email_client_credentials': email_client_credentials}, codes.OK


@api.route(EmailCampaignApi.EMAIL_CLIENT_WITH_ID)
class EmailClientsWithId(Resource):
    """
    This endpoint looks like /v1/email-clients/:id.
    We can get an email-client with its id in database table "email_client_credentials".
    """

    # Access token decorator
    decorators = [require_oauth()]

    def get(self, email_client_id):
        """
        This will get record from database table email_client_credentials for requested id.

        .. Response::
                       {
                          "email_client_credentials": {
                            "user_id": 1,
                            "name": "Gmail",
                            "updated_datetime": "2016-09-28 19:38:55",
                            "id": 69,
                            "port": "587",
                            "host": "smtp.gmail.com",
                            "password": "c2MAAh/OucvmgceAQ6qEFHpnDVm8wxsOGBo7+2iVToQSEQl8bSvMTjmhNTAj6phOaqDOI
                                        q5NQWHpvZG9SHZDINYORwGSTqSK4zyHOBiaxvjBkQ==",
                            "email": "gettalentmailtest@gmail.com"
                          }
                        }

        .. Status:: 200 (Resource Found)
                    400 (Bad request)
                    401 (Unauthorized to access getTalent)
                    403 (Unauthorized to access requested resource)
                    404 (Resource not found)
                    500 (Internal server error)
        """
        raise_if_dict_values_are_not_int_or_long(dict(email_client_id=email_client_id))
        client_in_db = EmailClientCredentials.get_by_id(email_client_id)
        if not client_in_db:
            raise ResourceNotFound(EMAIL_CLIENT_NOT_FOUND[0], error_code=EMAIL_CLIENT_NOT_FOUND[1])
        if not client_in_db.user.domain_id == request.user.domain_id:
            raise ForbiddenError(EMAIL_CLIENT_FORBIDDEN[0], error_code=EMAIL_CLIENT_FORBIDDEN[1])
        return {'email_client_credentials': client_in_db.to_json()}, codes.OK


@api.route(EmailCampaignApi.EMAIL_CONVERSATIONS)
class EmailConversations(Resource):
    """
    This endpoint deals with email-conversations for the added email-clients of users.
    """

    @require_oauth(allow_null_user=True)
    def post(self):
        """
        This endpoint will be hit by scheduler-service. It will loop over the entries in database table
        email_client_credentials for which server-type is "incoming" and will save the details of email-conversation
        in database table email-conversations.

        .. Status:: 401 (Unauthorized to access getTalent)
                    500 (Internal server error)
        """
        queue_name = EmailCampaign.__tablename__
        import_email_conversations.apply_async([queue_name], queue_name=queue_name)

    @require_oauth()
    def get(self):
        """
        This endpoint will return all the email-conversations in database table email-conversations for given user.

        .. Response::
            {
                "email_conversations":
                        [
                            {
                              "body": "Email campaign test",
                              "user_id": 1,
                              "updated_datetime": "2016-09-30 10:50:03",
                              "email_received_datetime": "2016-09-27 08:02:03",
                              "mailbox": "inbox",
                              "email_client_credentials": {
                                                            "id": 2,
                                                            "name": "Gmail"
                                                            },

                              "candidate_id": 4,
                              "id": 1,
                              "subject": "55b04894 It is a test campaign"
                            },
                            {
                              "body": "Email campaign test",
                              "user_id": 1,
                              "updated_datetime": "2016-09-30 10:50:05",
                              "email_received_datetime": "2016-09-27 08:01:48",
                              "mailbox": "inbox",
                              "email_client_credentials": {
                                                            "id": 2,
                                                            "name": "Gmail"
                                                            },
                              "candidate_id": 4,
                              "id": 2,
                              "subject": "37e0bd0b It is a test campaign"
                            },
                            {
                              "body": "Email campaign test",
                              "user_id": 1,
                              "updated_datetime": "2016-09-30 10:50:05",
                              "email_received_datetime": "2016-09-27 08:01:49",
                              "mailbox": "inbox",
                              "email_client_credentials": {
                                                            "id": 2,
                                                            "name": "Gmail"
                                                            },
                              "candidate_id": 4,
                              "id": 3,
                              "subject": "d5957c8e It is a test campaign"
                            }
                        ]
            }

        .. Status:: 401 (Unauthorized to access getTalent)
                    500 (Internal server error)
        """
        user = request.user
        email_conversations = [email_conversation.to_dict() for email_conversation in user.email_conversations]
        return {'email_conversations': email_conversations}, codes.OK


def schedule_job_for_email_conversations():
    """
    Schedule general job that hits /v1/email-conversations endpoint every hour.
    """
    url = EmailCampaignApiUrl.EMAIL_CONVERSATIONS
    task_name = 'get_email_conversations'
    start_datetime = datetime.utcnow() + timedelta(seconds=15)
    # Schedule for next 100 years
    end_datetime = datetime.utcnow() + timedelta(weeks=52 * 100)
    frequency = 3600
    access_token = User.generate_jw_token()
    headers = {'Content-Type': 'application/json',
               'Authorization': access_token}
    data = {
        'start_datetime': start_datetime.strftime(DatetimeUtils.ISO8601_FORMAT),
        'end_datetime': end_datetime.strftime(DatetimeUtils.ISO8601_FORMAT),
        'frequency': frequency,
        'is_jwt_request': True
    }

    logger.info('Checking if `{}` task already running...'.format(task_name))
    response = requests.get(SchedulerApiUrl.TASK_NAME % task_name, headers=headers)
    # If job is not scheduled then schedule it
    if response.status_code == requests.codes.NOT_FOUND:
        logger.info('Task `{}` not scheduled. Scheduling `{}` task.'.format(task_name, task_name))
        data.update({'url': url})
        data.update({'task_name': task_name, 'task_type': 'periodic'})
        response = requests.post(SchedulerApiUrl.TASKS, headers=headers, data=json.dumps(data))
        if response.status_code == codes.CREATED:
            logger.info('Task `{}` has been scheduled.'.format(task_name))
        elif response.json()['error']['code'] == TASK_ALREADY_SCHEDULED:
            logger.info('Job already scheduled. `{}`'.format(task_name))
        else:
            logger.error(response.text)
            raise InternalServerError(error_message='Unable to schedule job for getting email-conversations')
    elif response.status_code == requests.codes.ok:
        logger.info('Job already scheduled. `{}`'.format(response.text))
    else:
        logger.error(response.text)
