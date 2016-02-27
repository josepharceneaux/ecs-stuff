# Standard Imports
import time
import requests

# Application Specific
from email_campaign_service.common.models.db import db
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.models.user import DomainRole
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.email_campaign import (EmailCampaign,
                                                                 EmailClient)
from email_campaign_service.common.utils.handy_functions import add_role_to_test_user
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import \
    create_smartlist_from_api
from email_campaign_service.common.utils.candidate_service_calls import \
    create_candidates_from_candidate_api

__author__ = 'basit'


def create_email_campaign(user):
    """
    This creates an email campaign for given user
    :param user:
    :return:
    """
    email_campaign_name = fake.name()
    email_campaign_subject = fake.sentence()
    campaign_body_html = "<html><body>Email campaign test</body></html>"
    email_campaign = EmailCampaign(name=email_campaign_name,
                                   user_id=user.id,
                                   is_hidden=0,
                                   email_subject=email_campaign_subject,
                                   email_from=fake.safe_email(),
                                   email_reply_to=fake.email(),
                                   email_body_html=campaign_body_html,
                                   email_body_text="Email campaign test"
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


def create_email_campaign_smartlist(access_token, talent_pool, campaign,
                                    emails_list=True, count=1):
    """
    This associates smartlist ids with given campaign
    :param access_token:
    :param talent_pool:
    :param campaign:
    :return:
    """
    # create candidate
    smartlist_id, candidate_ids = create_smartlist_with_candidate(access_token,
                                                                  talent_pool,
                                                                  emails_list=emails_list,
                                                                  count=count)

    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign.id)
    return campaign


def create_smartlist_with_candidate(access_token, talent_pool, emails_list=True, count=1):
    """
    This creates candidate(s) as specified by the count,  and assign it to a smartlist.
    Finally it returns smartlist_id and candidate_ids.
    :param access_token:
    :param talent_pool:
    :param emails_list:
    :param count:
    :return:
    """
    # create candidate
    data = FakeCandidatesData.create(talent_pool=talent_pool, emails_list=emails_list, count=count)
    candidate_ids = create_candidates_from_candidate_api(access_token, data,
                                                         return_candidate_ids_only=True)
    smartlist_data = {'name': fake.word(),
                      'candidate_ids': candidate_ids}
    smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
    smartlist_id = smartlists['smartlist']['id']
    return smartlist_id, candidate_ids


def delete_campaign(campaign):
    """
    This deletes the campaign created during tests from database
    :param campaign:
    :return:
    """
    try:
        with app.app_context():
            if isinstance(campaign, dict):
                EmailCampaign.delete(campaign['id'])
            else:
                EmailCampaign.delete(campaign.id)
    except Exception:
        pass


def send_campaign(campaign, access_token):
    """
    This function sends the campaign via /v1/email-campaigns/:id/send
    :param campaign: Email campaign obj
    :param access_token: Auth token to make HTTP request
    :return:
    """
    # send campaign
    campaign.update(email_client_id=EmailClient.get_id_by_name('Browser'))
    response = requests.post(EmailCampaignUrl.SEND % campaign.id,
                             headers=dict(Authorization='Bearer %s' % access_token))
    assert response.ok
    time.sleep(20)
    db.session.commit()
