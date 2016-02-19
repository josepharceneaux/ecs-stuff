__author__ = 'basit'

from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import *
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.tests.modules.handy_functions import (create_email_campaign,
                                                                  assign_roles,
                                                                  create_email_campaign_smartlist,
                                                                  delete_campaign)


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
def assign_roles_to_user_first(user_first):
    """
    This assign required roles to user_first
    :param user_first:
    :return:
    """
    assign_roles(user_first)
