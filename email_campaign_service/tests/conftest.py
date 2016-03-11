__author__ = 'basit'

import re

from email_campaign_service.common.tests.conftest import *
from email_campaign_service.common.models.candidate import CandidateEmail
from email_campaign_service.common.models.email_campaign import EmailClient
from email_campaign_service.tests.modules.handy_functions import (create_email_campaign,
                                                                  assign_roles,
                                                                  create_email_campaign_smartlist,
                                                                  delete_campaign, send_campaign)


@pytest.fixture()
def email_campaign_of_user_first(request, user_first):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    """
    campaign = create_email_campaign(user_first)

    def fin():
        delete_campaign(campaign)

    request.addfinalizer(fin)
    return campaign


@pytest.fixture()
def email_campaign_of_user_second(request, user_same_domain):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    """
    campaign = create_email_campaign(user_same_domain)

    def fin():
        delete_campaign(campaign)

    request.addfinalizer(fin)
    return campaign


@pytest.fixture()
def email_campaign_in_other_domain(request,
                                   access_token_other,
                                   user_from_diff_domain,
                                   assign_roles_to_user_of_other_domain,
                                   talent_pool_other):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    for user in different domain
    """

    campaign = create_email_campaign(user_from_diff_domain)
    create_email_campaign_smartlist(access_token_other, talent_pool_other,
                                    campaign)

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
    """
    campaign = create_email_campaign_smartlist(access_token_first, talent_pool,
                                               email_campaign_of_user_first,
                                               emails_list=False)

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
    """
    assign_roles(user_first)


@pytest.fixture()
def assign_roles_to_user_of_other_domain(user_from_diff_domain):
    """
    This assigns required roles to user_from_diff_domain
    """
    assign_roles(user_from_diff_domain)


@pytest.fixture()
def candidate_in_other_domain(request, user_from_diff_domain):
    """
    Here we create a candidate for `user_from_diff_domain`
    """
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


@pytest.fixture(params=['with_client', 'without_client'])
def sent_campaign(request, campaign_with_valid_candidate, access_token_first):
    """
    This fixture sends the campaign 1) with client_id and 2) without client id
    via /v1/email-campaigns/:id/send and returns the email-campaign obj.
    """
    if request.param == 'with_client':
        campaign_with_valid_candidate.update(email_client_id=EmailClient.get_id_by_name('Browser'))
        sleep_time = 5
    else:
        sleep_time = 15
    # send campaign
    send_campaign(campaign_with_valid_candidate, access_token_first, sleep_time=sleep_time)
    return campaign_with_valid_candidate


@pytest.fixture()
def send_email_campaign_by_client_id_response(access_token_first, campaign_with_valid_candidate):
    """
    This fixture is used to get the response of sending campaign emails with client id
    for a particular campaign. It also ensures that response is in proper format. Used in
    multiple tests.
    :param access_token_first: Bearer token for authorization.
    :param campaign_with_valid_candidate: Email campaign object with a valid candidate associated.
    """
    campaign = campaign_with_valid_candidate
    campaign.update(email_client_id=EmailClient.get_id_by_name('Browser'))
    response = send_campaign(campaign_with_valid_candidate, access_token_first)
    json_response = response.json()
    assert 'email_campaign_sends' in json_response
    email_campaign_sends = json_response['email_campaign_sends'][0]
    assert 'new_html' in email_campaign_sends
    new_html = email_campaign_sends['new_html']
    matched = re.search(r'&\w+;', new_html)  # check the new_html for escaped HTML characters using regex
    assert not matched  # Fail if HTML escaped characters found, as they render the URL useless
    assert 'new_text' in email_campaign_sends  # Check if there is email text which candidate would see in email
    assert 'email_campaign_id' in email_campaign_sends  # Check if there is email campaign id in response
    assert campaign.id == email_campaign_sends['email_campaign_id']  # Check if both IDs are same
    return_value = dict()
    return_value['response'] = response
    return_value['campaign'] = campaign
    return return_value
