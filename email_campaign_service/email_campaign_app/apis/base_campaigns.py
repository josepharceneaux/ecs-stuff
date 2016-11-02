"""

 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have three endpoints

- POST /v1/base-campaigns to create a base campaign
- POST /v1/base-campaigns/:base_campaign_id/link-event/:event_id to associate an event with a base campaign
- GET /v1/base-campaigns/:base_campaign_id to get chained events abd campaigns

"""

__author__ = 'basit'

# Standard Library
import types

# Third Party
from requests import codes
from flask_restful import Resource
from flask import request, Blueprint

# Common utils
from email_campaign_service.common.models.event import Event
from email_campaign_service.common.talent_api import TalentApi
from email_campaign_service.common.routes import EmailCampaignApi
from email_campaign_service.common.utils.api_utils import api_route
from email_campaign_service.common.utils.auth_utils import require_oauth
from email_campaign_service.common.models.base_campaign import (BaseCampaign, BaseCampaignEvent)
from email_campaign_service.common.campaign_services.validators import validate_base_campaign_id
from email_campaign_service.common.error_handling import (InvalidUsage, ResourceNotFound, ForbiddenError)


# Blueprint for base-campaign API
base_campaign_blueprint = Blueprint('base_campaign_api', __name__)
api = TalentApi()
api.init_app(base_campaign_blueprint)
api.route = types.MethodType(api_route, api)


@api.route(EmailCampaignApi.BASE_CAMPAIGNS)
class BaseCampaigns(Resource):
    """
    This resource creates a base-campaign in database table base-campaign.
    """
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
        base_campaign_in_db = BaseCampaign.search_by_name_in_domain(domain_id=user.domain.id, name=name)
        if base_campaign_in_db:
            raise InvalidUsage('Campaign with same name found in database')
        base_campaign = BaseCampaign(user_id=user.id, name=name, description=description)
        base_campaign.save()
        return {'id': base_campaign.id}, codes.CREATED


@api.route(EmailCampaignApi.BASE_CAMPAIGN_EVENT)
class BaseCampaignLinkEvent(Resource):
    """
    This resource links an social-network event with base-campaign in database table base-campaign-event.
    """
    # Access token decorator
    decorators = [require_oauth()]

    def post(self, base_campaign_id, event_id):
        """
        This links an event with base-campaign.
        """
        event_in_db = Event.get_by_id(event_id)
        if not event_in_db:
            raise ResourceNotFound('Requested event not found in database')
        is_user_owner = Event.get_by_user_and_event_id(request.user.id, event_id)
        if not is_user_owner:
            raise ForbiddenError('Requested event does not belong to requested user')
        validate_base_campaign_id(base_campaign_id, request.user.domain_id)
        record_in_db = BaseCampaignEvent.filter_by_keywords(base_campaign_id=base_campaign_id, event_id=event_id)
        if record_in_db:
            return {'id': record_in_db.id}
        base_campaign_event = BaseCampaignEvent(base_campaign_id=base_campaign_id, event_id=event_id)
        base_campaign_event.save()
        return {'id': base_campaign_event.id}, codes.CREATED


@api.route(EmailCampaignApi.BASE_CAMPAIGN)
class BaseCampaignOverview(Resource):
    """
    This resource returns event and all chained campaigns with given base_campaign_id
    """
    # Access token decorator
    decorators = [require_oauth()]

    def get(self, base_campaign_id):
        """
        This resource returns event and all chained campaigns with given base_campaign_id.
        ..Response::

            {
                 "event_details": {
                        "event": {
                              "cost": 0,
                              "start_datetime": "2016-08-13 16:21:42",
                              "venue_id": 307,
                              "user_id": 1,
                              "description": "Test Event Description",
                              "social_network_id": 13,
                              "url": "",
                              "title": "Eventbrite Test Event",
                              "registration_instruction": "Just Come",
                              "max_attendees": 10,
                              "timezone": "Asia/Karachi",
                              "currency": "USD",
                              "tickets_id": 53364240,
                              "social_network_group_id": "18837246",
                              "group_url_name": "QC-Python-Learning",
                              "organizer_id": 33,
                              "base_campaign_id": 1,
                              "id": 1,
                              "social_network_event_id": "27067814562",
                              "end_datetime": "2016-08-14 16:21:42"
                            },
                        "rsvps": [
                              {
                                "social_network_rsvp_id": "6956",
                                "status": "yes",
                                "social_network_id": 13,
                                "event_id": 1,
                                "payment_status": "",
                                "datetime": "",
                                "candidate_id": 362553,
                                "id": 2
                              },
                              {
                                "social_network_rsvp_id": "2983",
                                "status": "yes",
                                "social_network_id": 13,
                                "event_id": 1,
                                "payment_status": "",
                                "datetime": "",
                                "candidate_id": 362555,
                                "id": 3
                              },
                              {
                                "social_network_rsvp_id": "5146",
                                "status": "yes",
                                "social_network_id": 13,
                                "event_id": 1,
                                "payment_status": "",
                                "datetime": "",
                                "candidate_id": 362557,
                                "id": 4
                              }
                            ]
                        },
                "email_campaigns": [
                      {
                          "blasts": [
                                {
                                  "updated_datetime": "2016-02-10 20:35:57",
                                  "sends": 1000,
                                  "bounces": 50,
                                  "campaign_id": 11,
                                  "text_clicks": 155,
                                  "html_clicks": 876,
                                  "complaints": 0,
                                  "id": 15,
                                  "opens": 900,
                                  "sent_datetime": "2016-02-10 20:38:39"
                                },
                                {
                                  "updated_datetime": "2016-02-10 20:35:57",
                                  "sends": 200,
                                  "bounces": 112,
                                  "campaign_id": 11,
                                  "text_clicks": 0,
                                  "html_clicks": 0,
                                  "complaints": 0,
                                  "id": 17,
                                  "opens": 134,
                                  "sent_datetime": "2016-02-10 20:38:42"
                                }
                              ],
                          "email_campaign": {
                                            "email_client_credentials_id": null,
                                            "start_datetime": null,
                                            "user_id": 1,
                                            "name": "Email campaign",
                                            "body_text": null,
                                            "description": null,
                                            "list_ids": [1],
                                            "body_html": null,
                                            "added_datetime": "2016-02-10T20:35:57+00:00",
                                            "frequency": null,
                                            "end_datetime": null,
                                            "talent_pipelines": [],
                                            "reply_to": "basit.gettalent@gmail.com",
                                            "from": "basit",
                                            "is_hidden": false,
                                            "base_campaign_id": 1,
                                            "id": 11,
                                            "subject": "email campaign sample subject"
                                          }
                      },
                      {
                           "blasts": [
                                {
                                  "updated_datetime": "2016-02-10 20:39:54",
                                  "sends": 1,
                                  "bounces": 0,
                                  "campaign_id": 12,
                                  "text_clicks": 0,
                                  "html_clicks": 0,
                                  "complaints": 0,
                                  "id": 18,
                                  "opens": 0,
                                  "sent_datetime": "2016-02-10 20:39:44"
                                }
                              ],
                           "email_campaign": {
                                                "email_client_credentials_id": null,
                                                "start_datetime": null,
                                                "user_id": 1,
                                                "name": "Email campaign",
                                                "body_text": null,
                                                "description": null,
                                                "list_ids": [1],
                                                "body_html": null,
                                                "added_datetime": "2016-02-10T20:35:57+00:00",
                                                "frequency": null,
                                                "end_datetime": null,
                                                "talent_pipelines": [],
                                                "reply_to": "basit.gettalent@gmail.com",
                                                "from": "basit",
                                                "is_hidden": false,
                                                "base_campaign_id": 1,
                                                "id": 12,
                                                "subject": "email campaign sample subject"
                                              }
                                }
                           ]
            }
        """
        event_details = None
        validate_base_campaign_id(base_campaign_id, request.user.domain_id)
        base_campaign = BaseCampaign.get_by_id(base_campaign_id)
        base_campaign_event = BaseCampaignEvent.filter_by_keywords(base_campaign_id=base_campaign_id)
        if base_campaign_event:
            event = base_campaign_event[0].event  # Pick first associated event
            event_details = {'event': event.to_json(),
                             'rsvps': [rsvp.to_json() for rsvp in event.rsvps.all()]}
        email_campaigns = base_campaign.email_campaigns
        if not event_details and not email_campaigns:
            raise InvalidUsage('Requested base campaign is orphaned')
        email_campaigns_data = [{'email_campaign': email_campaign.to_dict(),
                                 'blasts': [blast.to_json() for blast in email_campaign.blasts.all()]}
                                for email_campaign in email_campaigns.all()]
        return {'event_details': event_details,
                'email_campaigns': email_campaigns_data}
