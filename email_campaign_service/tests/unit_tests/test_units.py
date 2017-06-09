"""
Here are the unit test for email-campaign-service
"""
import requests
from contracts import ContractNotRespected
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.error_handling import InvalidUsage
from email_campaign_service.common.routes import EmailCampaignApiUrl, HEALTH_CHECK
from email_campaign_service.modules.utils import do_mergetag_replacements, TEST_PREFERENCE_URL
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.tests.modules.handy_functions import create_email_campaign_with_merge_tags

__author__ = 'basit'


def test_mergetag_replacements(user_first, candidate_first):
    """
    Here we test the functionality of function do_mergetag_replacement()
    """
    # Merge tags for user
    campaign = create_email_campaign_with_merge_tags(user_id=user_first.id, in_db_only=True)
    user_first.update(first_name=fake.first_name())
    user_first.update(last_name=fake.last_name())
    [subject, body_text, body_html] = do_mergetag_replacements([campaign.subject, campaign.body_text,
                                                                campaign.body_html], user_first,
                                                               requested_object=user_first)
    for item in [subject, body_text, body_html]:
        assert user_first.first_name in item
        assert user_first.last_name in item
        assert user_first.name in item

    for item in [body_text, body_html]:
        assert TEST_PREFERENCE_URL in item
    # Merge tags for candidate
    campaign = create_email_campaign_with_merge_tags(user_id=user_first.id, in_db_only=True)

    [subject, body_text, body_html] = do_mergetag_replacements([campaign.subject, campaign.body_text,
                                                                campaign.body_html], user_first,
                                                               requested_object=candidate_first)
    for item in [subject, body_text, body_html]:
        assert candidate_first.first_name in item
        assert candidate_first.last_name in item

    for item in [body_text, body_html]:
        assert str(candidate_first.id) in item
        assert user_first.name in item

    # Test with invalid object(i.e. other than user or candidate)
    try:
        do_mergetag_replacements([campaign.subject], campaign)
        assert None, 'It should raise Invalid usage error'
    except InvalidUsage as error:
        assert 'Invalid' in error.message

    # Test with non-list item as first argument
    for invalid_param in CampaignsTestsHelpers.INVALID_STRING:
        try:
            do_mergetag_replacements(invalid_param, user_first)
            assert None, 'It should raise ContractNotRespected exception for param:%s' % invalid_param
        except ContractNotRespected as error:
            assert error.error


def test_candidate_name(candidate_first):
    """
    Here we test different scenarios for Candidate model's property name().
    """
    first_name = fake.first_name()
    last_name = fake.last_name()

    # Test with first_name and last_name as None
    candidate_first.update(first_name=None)
    candidate_first.update(last_name=None)
    assert candidate_first.name == ''

    # Test with non-empty first_name and last_name as None
    candidate_first.update(first_name=first_name)
    candidate_first.update(last_name=None)
    assert candidate_first.name == first_name

    # Test with first_name as None and non-empty last_name
    candidate_first.update(first_name=None)
    candidate_first.update(last_name=last_name)
    assert candidate_first.name == last_name

    # Test with non-empty first_name and non-empty last_name
    candidate_first.update(first_name=first_name)
    candidate_first.update(last_name=last_name)
    assert candidate_first.name == first_name + ' ' + last_name


# Test for healthcheck
def test_health_check():
    response = requests.get(EmailCampaignApiUrl.HOST_NAME % HEALTH_CHECK)
    assert response.status_code == requests.codes.OK

    # Testing Health Check URL with trailing slash
    response = requests.get(EmailCampaignApiUrl.HOST_NAME % HEALTH_CHECK + '/')
    assert response.status_code == requests.codes.OK