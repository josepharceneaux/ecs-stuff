"""

 Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

Here we have three endpoints

- POST /v1/base-campaigns to create a base campaign
- POST /v1/base-campaigns/:base_campaign_id/link-event/:event_id to associate an event with a base campaign
- GET /v1/base-campaigns/:base_campaign_id to get chained events and campaigns(email, sms, push etc)

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
        is_event_in_domain = Event.get_by_event_id_and_domain_id(event_id, request.user.domain_id)
        if not is_event_in_domain:
            raise ForbiddenError('Requested event does not belong to requested user`s domain')
        validate_base_campaign_id(base_campaign_id, request.user.domain_id)
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
                "venue": {
                              "city": "Lahore",
                              "user_id": 1,
                              "social_network_id": 18,
                              "country": "",
                              "longitude": 0,
                              "social_network_venue_id": "16271034",
                              "state": "Punjab",
                              "latitude": 0,
                              "zip_code": "",
                              "address_line_2": "H# 163, Block A",
                              "id": 307,
                              "address_line_1": "New Muslim Town"
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
                        ],
                "tickets_id": 53364240,
                "social_network_group_id": "18837246",
                "group_url_name": "QC-Python-Learning",
                "organizer_id": 33,
                "base_campaign_id": 1,
                "id": 1,
                "social_network_event_id": "27067814562",
                "end_datetime": "2016-08-14 16:21:42"
              },
        "email_campaigns": [
                {
                      "email_client_credentials_id": null,
                      "start_datetime": null,
                      "user_id": 1,
                      "name": "Email campaign",
                      "body_text": null,
                      "description": null,
                      "list_ids": [1],
                      "body_html": null,
                      "blasts": [
                            {
                              "updated_datetime": "2016-02-10 20:35:57",
                              "sends": 0,
                              "bounces": 0,
                              "campaign_id": 11,
                              "text_clicks": 0,
                              "html_clicks": 0,
                              "complaints": 0,
                              "id": 15,
                              "opens": 0,
                              "sent_datetime": "2016-02-10 20:38:39"
                            },
                            {
                              "updated_datetime": "2016-02-10 20:35:57",
                              "sends": 0,
                              "bounces": 0,
                              "campaign_id": 11,
                              "text_clicks": 0,
                              "html_clicks": 0,
                              "complaints": 0,
                              "id": 16,
                              "opens": 0,
                              "sent_datetime": "2016-02-10 20:38:40"
                            }
                          ],
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
                    },
                {
                      "email_client_credentials_id": null,
                      "start_datetime": null,
                      "user_id": 1,
                      "name": "Email campaign",
                      "body_text": null,
                      "description": null,
                      "list_ids": [1],
                      "body_html": null,
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
              ]
        }
        """
        json_event = None
        email_campaigns_list = []
        validate_base_campaign_id(base_campaign_id, request.user.domain_id)
        base_campaign = BaseCampaign.get_by_id(base_campaign_id)
        base_campaign_event = BaseCampaignEvent.filter_by_keywords(base_campaign_id=base_campaign_id)
        if base_campaign_event:
            event = base_campaign_event[0].event  # Pick first associated event
            json_event = event.to_json()
            json_event['rsvps'] = [rsvp.to_json() for rsvp in event.rsvps.all()]
            json_event['venue'] = event.venue.to_json() if event.venue else {}
        email_campaigns = base_campaign.email_campaigns.all()
        if not json_event and not email_campaigns:
            raise InvalidUsage('Requested base campaign is orphaned')
        for email_campaign in email_campaigns:
            json_email_campaign = email_campaign.to_dict()
            json_email_campaign['blasts'] = [blast.to_json() for blast in email_campaign.blasts.all()]
            email_campaigns_list.append(json_email_campaign)
        return {'event': json_event, 'email_campaigns': email_campaigns_list}
