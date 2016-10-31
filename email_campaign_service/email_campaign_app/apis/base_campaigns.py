"""

 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have three endpoints

- POST /v1/base-campaigns to create a base campaign
- POST /v1/base-campaigns/:base_campaign_id/link-event/:event_id to associate an event with a base campaign
- GET /v1/base-campaigns/:id to get all the chained events and campaigns (email, SMS, push etc)

"""

__author__ = 'basit'

# Standard Library
import types

# Third Party
from flask_restful import Resource
from flask import request, Blueprint

# Common utils
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignApi
from email_campaign_service.common.utils.api_utils import api_route
from email_campaign_service.common.error_handling import InvalidUsage
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.models.base_campaign import BaseCampaign


# Blueprint for base-campaign API
base_campaign_blueprint = Blueprint('base_campaign_api', __name__)
api = TalentApi()
api.init_app(base_campaign_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(EmailCampaignApi.BASE_CAMPAIGNS)
class EmailCampaigns(Resource):

    # Access token decorator
    decorators = [require_oauth()]

    def post(self):
        """
        This creates a base campaign with following payload

                {
                    "name": "Jobs at getTalent
                    "Description": "We are looking for Python developers
                }

        """
        user = request.user
        data = request.get_json(silent=True)
        if not data:
            raise InvalidUsage("Received empty request body")
        name = data.get('name', '')
        description = data.get('description', '')
        if not name or not description:
            raise InvalidUsage('Name and description are required fields')
        base_campaign_in_db = BaseCampaign.filter_by_keywords(user_id=user.id, name=name)
        if base_campaign_in_db:
            raise InvalidUsage('Campaign with same name found in database')
        base_campaign = BaseCampaign(user_id=user.id, name=name, description=description)
        base_campaign.save()
        return {'id': base_campaign.id}
