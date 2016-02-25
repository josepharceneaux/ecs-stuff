
__author__ = 'basit'
import re

from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import *
from email_campaign_service.common.models.candidate import CandidateEmail
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.tests.modules.handy_functions import (create_email_campaign,
                                                                  assign_roles,
                                                                  create_email_campaign_smartlist,
                                                                  delete_campaign)
from email_campaign_service.common.models.email_campaign import EmailCampaign, EmailClient
from email_campaign_service.common.routes import EmailCampaignUrl


@pytest.fixture()
def email_campaign_of_user_first(request, user_first):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    :param user_first:
    :return:
    """
    campaign = create_email_campaign(user_first)

    def fin():
        delete_campaign(campaign)

    request.addfinalizer(fin)
    return campaign


@pytest.fixture()
def email_campaign_in_other_domain(request, user_from_diff_domain,
                                   campaign_with_candidate_having_no_email):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    for user in different domain
    :return:
    """
    campaign = create_email_campaign(user_from_diff_domain)
    smartlist_id = campaign_with_candidate_having_no_email.smartlists[0].smartlist_id
    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign.id)

    def fin():
        delete_campaign(campaign)

    request.addfinalizer(fin)
    return campaign


@pytest.fixture()
def campaign_with_candidate_having_no_email(request, email_campaign_of_user_first,
                                            assign_roles_to_user_first,
                                            access_token_first, talent_pool):
    """
    This creates a campaign which has candidates associated having no email
    :param email_campaign_of_user_first:
    :return:
    """
    campaign = create_email_campaign_smartlist(access_token_first, talent_pool,
                                               email_campaign_of_user_first, emails_list=False)

    def fin():
        delete_campaign(campaign)

    request.addfinalizer(fin)
    return campaign


@pytest.fixture()
def campaign_with_valid_candidate(request, email_campaign_of_user_first,
                                  assign_roles_to_user_first,
                                  access_token_first, talent_pool):
    """
    This returns a campaign which has one candidate associated having email address.
    :param email_campaign_of_user_first:
    :return:
    """
    campaign = create_email_campaign_smartlist(access_token_first, talent_pool,
                                               email_campaign_of_user_first, count=2)

    def fin():
        delete_campaign(campaign)

    request.addfinalizer(fin)
    return campaign


@pytest.fixture()
def campaign_with_candidates_having_same_email_in_diff_domain(request,
                                                              campaign_with_valid_candidate,
                                                              candidate_in_other_domain,
                                                              assign_roles_to_user_first):
    """
    This returns a campaign which has one candidate associated having email address.
    One more candidate exist in some other domain having same email address.
    :return:
    """
    same_email = fake.email()
    campaign_with_valid_candidate.user.candidates[0].emails[0].update(address=same_email)
    candidate_in_other_domain.emails[0].update(address=same_email)

    def fin():
        delete_campaign(campaign_with_valid_candidate)
    request.addfinalizer(fin)
    return campaign_with_valid_candidate


@pytest.fixture()
def assign_roles_to_user_first(user_first):
    """
    This assign required roles to user_first
    :param user_first:
    :return:
    """
    assign_roles(user_first)


@pytest.fixture()
def candidate_in_other_domain(request, user_from_diff_domain):
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20),
                          user_id=user_from_diff_domain.id)
    Candidate.save(candidate)
    candidate_email = CandidateEmail(candidate_id=candidate.id,
                                     address=gen_salt(20), email_label_id=1)
    CandidateEmail.save(candidate_email)

    def tear_down():
        try:
            Candidate.delete(candidate)
        except Exception:
            db.session.rollback()
    request.addfinalizer(tear_down)
    return candidate
@pytest.fixture()
def send_email_campaign_by_client_id_response(access_token_first, campaign_with_valid_candidate):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    for user in different domain
    :param access_token_first:
    :param campaign_with_valid_candidate:
    :return:
    :return:
    """
    URL = EmailCampaignUrl.SEND
    campaign = EmailCampaign.get_by_id(str(campaign_with_valid_candidate.id))
    campaign.update(email_client_id=EmailClient.get_id_by_name('Browser'))
    response = requests.post(
        URL % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
    assert response.status_code == 200
    json_response = response.json()
    assert 'email_campaign_sends' in json_response
    email_campaign_sends = json_response['email_campaign_sends'][0]
    assert 'new_html' in email_campaign_sends
    new_html = email_campaign_sends['new_html']
    matched = re.search(r'&\w+;', new_html)
    assert not matched
    assert 'new_text' in email_campaign_sends
    assert 'email_campaign_id' in email_campaign_sends
    assert campaign.id == email_campaign_sends['email_campaign_id']
    return_value = dict()
    return_value['response'] = response
    return_value['campaign'] = campaign
    return return_value