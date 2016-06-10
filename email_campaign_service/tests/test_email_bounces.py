"""
Author: Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com>

    This module contains pyTests for send an email campaign to invalid emails and
    then expecting bounce messages from Amazon SNS which will mark invalid email as bounced.
"""

from redo import retry

from email_campaign_service.common.models.candidate import CandidateEmail
from email_campaign_service.common.tests.conftest import *

from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.email_campaign import EmailCampaignBlast
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.campaign_services.custom_errors import CampaignException
from email_campaign_service.tests.modules.handy_functions import send_campaign_email_to_candidate
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers


@pytest.mark.parametrize("blast_foreign_key", [True, False])
def test_send_campaign_to_invalid_email_address(access_token_first, assign_roles_to_user_first, email_campaign_of_user_first,
                                                candidate_first, user_first, talent_pipeline, blast_foreign_key):
    """
    In this test, we will send an email campaign to one candidate with invalid email address.
    After bounce, this email will be marked as bounced and when we will try to send this campaign
    through API, it will raise InvalidUsage because no valid candidate is associated with this campaign.
    """
    with app.app_context():
        campaign = email_campaign_of_user_first
        # create candidate
        email_campaign_blast, smartlist_id, candidate_ids = create_campaign_data(access_token_first, campaign.id,
                                                                                 talent_pipeline, candidate_count=1)

        invalid_email = 'invalid_' + fake.uuid4() + '@gmail.com'
        email = CandidateEmail.get_email_by_candidate_id(candidate_ids[0])
        email.update(address=invalid_email)
        db.session.commit()
        if blast_foreign_key:
            send_campaign_email_to_candidate(campaign, email, candidate_ids[0], blast_id=email_campaign_blast.id)
        else:
            send_campaign_email_to_candidate(campaign, email, candidate_ids[0], blast_id=None)

        retry(check_is_bounced, sleeptime=3, attempts=33, sleepscale=1,
              args=(email,), retry_exceptions=(AssertionError,))
        campaign_blasts = CampaignsTestsHelpers.get_blasts_with_polling(campaign, timeout=20)

        campaign_blast = campaign_blasts[0]
        assert campaign_blast.bounces == 1

        # Since there is no candidate associated with campaign with valid email, so no more blasts would be created
        response = requests.post(
            EmailCampaignApiUrl.SEND % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == 200
        retry(CampaignsTestsHelpers.verify_blasts, sleeptime=3, attempts=100, sleepscale=1,
              args=(campaign, access_token_first, None, 1), retry_exceptions=(AssertionError,))


def check_is_bounced(email):
    """
    Checks if a candidate
    :param email: candidate email
    :return: value of is_bounced (0 or 1)
    """
    db.session.commit()
    assert email.is_bounced
    return email.is_bounced


def test_send_campaign_to_valid_and_invalid_email_address(access_token_first, assign_roles_to_user_first,
                                                          email_campaign_of_user_first,candidate_first,
                                                          user_first, talent_pipeline):
    """
    In this test we are sending emails to two candidate, one with valid email and one with invalid email.
    After sending emails, we will confirm that invalid email has been marked `bounced` and will assert
    email campaign blasts and send accordingly.

    We will then send this campaign through API and we will confirm that email was sent to only one candidate
    with valid candidate, so there will be only one campaign send while there are two candidates are
    associated with this campaign.
    """
    with app.app_context():
        count = 2
        campaign = email_campaign_of_user_first

        # create candidate, smartlist and campaign blast
        email_campaign_blast, smartlist_id, candidate_ids = create_campaign_data(access_token_first, campaign.id,
                                                                                 talent_pipeline, candidate_count=count)

        # Update first candidate's email to a valid email, i.e. testing email.
        valid_email = 'gettalentmailtest@gmail.com'
        email = CandidateEmail.get_email_by_candidate_id(candidate_id=candidate_ids[0])
        email.update(address=valid_email)

        # Update second candidate's email to an invalid email, so we can test email bounce
        invalid_email = 'invalid_' + fake.uuid4() + '@gmail.com'
        email = CandidateEmail.get_email_by_candidate_id(candidate_id=candidate_ids[1])
        email.update(address=invalid_email)
        db.session.commit()

        for index in range(count):
            email = CandidateEmail.get_email_by_candidate_id(candidate_id=candidate_ids[index])
            send_campaign_email_to_candidate(campaign, email, candidate_ids[index], email_campaign_blast.id)
        retry(check_is_bounced, sleeptime=3, attempts=33, sleepscale=1,
              args=(email,), retry_exceptions=(AssertionError,))

        campaign_blasts = campaign.blasts.all()
        assert len(campaign_blasts) == 1
        campaign_blast = campaign_blasts[0]

        # There should be one bounce for this campaign blast.
        assert campaign_blast.bounces == 1

        blast_sends = campaign_blast.blast_sends.all()
        assert len(blast_sends) == 2
        assert blast_sends[0].is_ses_bounce is False
        assert blast_sends[1].is_ses_bounce is True
        # Now send this campaign through API, and there should be two blasts and Only one send associated with
        # this campaign because email has been marked as bounced.
        response = requests.post(
            EmailCampaignApiUrl.SEND % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == 200
        retry(CampaignsTestsHelpers.verify_blasts, sleeptime=3, attempts=100, sleepscale=1,
              args=(campaign, access_token_first, None, 2), retry_exceptions=(AssertionError,))

        CampaignsTestsHelpers.assert_blast_sends(campaign, 1, blast_index=1, abort_time_for_sends=200)
        db.session.commit()
        campaign_blasts = campaign.blasts.all()
        # Get second blast
        campaign_blast = campaign_blasts[1]

        # There is no bounces next time, because email was not sent to invalid (bounced) email.
        assert campaign_blast.bounces == 0

        # Email was sent to only one candidate
        assert campaign_blast.sends == 1

        blast_sends = campaign_blast.blast_sends.all()
        assert len(blast_sends) == 1
        assert blast_sends[0].is_ses_bounce is False


def create_campaign_data(access_token, campaign_id, talent_pipeline, candidate_count=1):
    """
    This functions creates initial data to send a campaign.
        - It creates candidate and associates this candidate to a new smartlist
        - It then creates campaign blast
        - It returns a tuple with campaign blast, smartlist_id, candidate_ids
    """
    smartlist_id, candidate_ids = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token,
                                                                                        talent_pipeline,
                                                                                        emails_list=True,
                                                                                        count=candidate_count)

    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign_id)
    email_campaign_blast = EmailCampaignBlast(campaign_id=campaign_id,
                                              sent_datetime=datetime.now())
    EmailCampaignBlast.save(email_campaign_blast)
    return email_campaign_blast, smartlist_id, candidate_ids
