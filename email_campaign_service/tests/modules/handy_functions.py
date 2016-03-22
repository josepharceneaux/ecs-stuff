# Standard Imports
import json
import time
import requests

# Application Specific
from email_campaign_service.common.models.db import db
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.models.user import DomainRole
from email_campaign_service.common.routes import (EmailCampaignUrl,
                                                  CandidatePoolApiUrl)
from email_campaign_service.common.models.email_campaign import EmailCampaign
from email_campaign_service.common.utils.handy_functions import (add_role_to_test_user,
                                                                 raise_if_not_instance_of)
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import \
    create_smartlist_from_api
from email_campaign_service.common.utils.candidate_service_calls import \
    create_candidates_from_candidate_api
from __init__ import ALL_EMAIL_CAMPAIGN_FIELDS

__author__ = 'basit'


def create_email_campaign(user):
    """
    This creates an email campaign for given user
    """
    email_campaign_name = fake.name()
    email_campaign_subject = fake.sentence()
    campaign_body_html = "<html><body>Email campaign test</body></html>"
    email_campaign = EmailCampaign(name=email_campaign_name,
                                   user_id=user.id,
                                   is_hidden=0,
                                   subject=email_campaign_subject,
                                   _from=fake.safe_email(),
                                   reply_to=fake.email(),
                                   body_html=campaign_body_html,
                                   body_text="Email campaign test"
                                   )
    EmailCampaign.save(email_campaign)
    return email_campaign


def assign_roles(user):
    """
    This assign required permission to given user
    :param user:
    :return:
    """
    add_role_to_test_user(user, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                 DomainRole.Roles.CAN_GET_CANDIDATES])


def create_email_campaign_smartlist(access_token, talent_pipeline, campaign,
                                    emails_list=True, count=1):
    """
    This associates smartlist ids with given campaign
    """
    # create candidate
    smartlist_id, candidate_ids = create_smartlist_with_candidate(access_token,
                                                                  talent_pipeline,
                                                                  emails_list=emails_list,
                                                                  count=count)

    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign.id)
    return campaign


def create_smartlist_with_candidate(access_token, talent_pipeline, emails_list=True, count=1):
    """
    This creates candidate(s) as specified by the count,  and assign it to a smartlist.
    Finally it returns smartlist_id and candidate_ids.
    """
    # create candidate
    data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool,
                                     emails_list=emails_list, count=count)
    candidate_ids = create_candidates_from_candidate_api(access_token, data,
                                                         return_candidate_ids_only=True)
    smartlist_data = {'name': fake.word(),
                      'candidate_ids': candidate_ids,
                      'talent_pipeline_id': talent_pipeline.id}
    smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
    smartlist_id = smartlists['smartlist']['id']
    return smartlist_id, candidate_ids


def delete_campaign(campaign):
    """
    This deletes the campaign created during tests from database
    :param campaign: Email campaign object
    """
    try:
        with app.app_context():
            if isinstance(campaign, dict):
                EmailCampaign.delete(campaign['id'])
            else:
                EmailCampaign.delete(campaign.id)
    except Exception:
        pass


def send_campaign(campaign, access_token, sleep_time=20):
    """
    This function sends the campaign via /v1/email-campaigns/:id/send
    sleep_time is set to be 20s here. One can modify this by passing required value.
    :param campaign: Email campaign obj
    :param access_token: Auth token to make HTTP request
    :param sleep_time: time in seconds to wait for the task to be run on Celery.
    """
    raise_if_not_instance_of(campaign, EmailCampaign)
    raise_if_not_instance_of(access_token, basestring)
    # send campaign
    response = requests.post(EmailCampaignUrl.SEND % campaign.id,
                             headers=dict(Authorization='Bearer %s' % access_token))
    assert response.ok
    time.sleep(sleep_time)
    db.session.commit()
    return response


def assert_valid_campaign_get(email_campaign_dict, referenced_campaign, fields=None):
    """
    This asserts that the campaign we get from GET call has valid values as we have for
    referenced email-campaign.
    :param dict email_campaign_dict: EmailCampaign object as received by GET call
    :param referenced_campaign: EmailCampaign object by which we compare the campaign
            we GET in response
    :param list[str] fields: List of fields that the campaign should have, or all of them if None
    """

    # Assert the fields are correct
    expected_email_campaign_fields_set = set(fields or ALL_EMAIL_CAMPAIGN_FIELDS)
    actual_email_campaign_fields_set = set(email_campaign_dict.keys())
    assert expected_email_campaign_fields_set == actual_email_campaign_fields_set, \
        "Response's email campaign fields (%s) should match the expected email campaign fields (%s)" % (
            actual_email_campaign_fields_set, expected_email_campaign_fields_set
        )

    # Assert id is correct, if returned by API
    if 'id' in expected_email_campaign_fields_set:
        assert email_campaign_dict['id'] == referenced_campaign.id


def get_campaign_or_campaigns(access_token, campaign_id=None, fields=None, pagination_query=None):
    """
    This makes HTTP GET call on /v1/email-campaigns with given access_token to get
    1) all the campaigns of logged-in user if campaign_id is None
    2) Get campaign object for given campaign_id
    :param list[str] fields: List of EmailCampaign fields to retrieve
    """
    if campaign_id:
        url = EmailCampaignUrl.CAMPAIGN % campaign_id
        entity = 'email_campaign'
    else:
        url = EmailCampaignUrl.CAMPAIGNS
        entity = 'email_campaigns'
    if pagination_query:
        url = url + pagination_query

    params = {'fields': ','.join(fields)} if fields else {}
    response = requests.get(url=url,
                            params=params,
                            headers={'Authorization': 'Bearer %s' % access_token})
    assert response.status_code == 200
    resp = response.json()
    assert entity in resp
    return resp[entity]


def assert_talent_pipeline_response(talent_pipeline, access_token, fields=None):
    """
    This makes HTTP GET call on candidate_pool_service to get response for given
    talent_pipeline and then asserts if we get an OK response.
    :param list[str] fields:  List of fields each EmailCampaign should have.  If None, will assert on all fields.
    """
    params = {'fields': ','.join(fields)} if fields else {}
    response = requests.get(
        url=CandidatePoolApiUrl.TALENT_PIPELINE_CAMPAIGN % talent_pipeline.id,
        params=params,
        headers={'Authorization': 'Bearer %s' % access_token})
    assert response.status_code == 200
    resp = response.json()
    print "Response JSON: %s" % json.dumps(resp)
    assert 'email_campaigns' in resp, "Response dict should have email_campaigns key"

    # Assert on the existence of email campaign fields
    for email_campaign_dict in resp['email_campaigns']:
        expected_email_campaign_fields_set = set(fields or ALL_EMAIL_CAMPAIGN_FIELDS)
        actual_email_campaign_fields_set = set(email_campaign_dict.keys())
        assert expected_email_campaign_fields_set == actual_email_campaign_fields_set, \
            "Response's email campaign fields should match the expected email campaign fields"
