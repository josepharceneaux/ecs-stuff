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
import types

# Third Party
import requests
from flask_restful import Resource
from flask import request, Blueprint

# Service Specific
from email_campaign_service.common.utils.validators import get_json_data_if_validated
from email_campaign_service.email_campaign_app import logger
from email_campaign_service.json_schema.email_clients import EMAIL_CLIENTS_SCHEMA
from email_campaign_service.json_schema.test_email import TEST_EMAIL_SCHEMA
from email_campaign_service.modules.utils import SMTP, IMAP, POP
from email_campaign_service.modules.validations import validate_and_format_request_data, validate_email_client_data

# Common utils
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignApi
from email_campaign_service.common.utils.api_utils import api_route
from email_campaign_service.common.error_handling import InvalidUsage
from email_campaign_service.common.utils.auth_utils import require_oauth

# Blueprint for email-clients API
email_clients_blueprint = Blueprint('email_clients_api', __name__)
api = TalentApi()
api.init_app(email_clients_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(EmailCampaignApi.CLIENTS)
class EmailClients(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    def post(self):
        """
        This will save an entry in database table email_client_credentials.

        .. Request Body::
                        {
                            "host": "server_name",
                            "port": 123,
                            "email": "email",
                            "password": "password",
                            "type": "incoming" or "outgoing",
                            "incoming_server_type": "IMAP" or "POP"
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
        validate_email_client_data(data)
        user_id = request.user.id
        if 'smtp' in data['host']:
            client_object = SMTP(data['host'], data['port'], data['email'], data['password'])
            client_object.connect()
        elif 'imap' in data['host']:
            client_object = IMAP(data['host'], data['port'], data['email'], data['password'])
            client_object.connect()
        elif 'pop' in data['host']:
            client_object = POP(data['host'], data['port'], data['email'], data['password'])
            client_object.connect()
        else:
            raise InvalidUsage('Unknown host provided')

        return {'id': ''}, requests.codes.CREATED


@api.route(EmailCampaignApi.CONVERSATIONS)
class EmailConversations(Resource):

    # Access token decorator
    decorators = [require_oauth(allow_null_user=True)]

    def post(self):
        """
        This endpoint will be hit by scheduler-service. It will loop over the entries in database table
        email_client_credentials for which server-type is incoming and will save the details of email-conversation
        in database table email-conversations.

        .. Status:: 401 (Unauthorized to access getTalent)
                    500 (Internal server error)
        """
        pass