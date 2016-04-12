"""
Author: Zohaib Ijaz, QC-Technologies, <mzohaib.qc@gmail.com>

    This module contains pyTests for send an email campaign to invalid emails and
    then expecting bounce messages from Amazon SNS which will mark invalid email as bounced.
"""
import time

from email_campaign_service.common.campaign_services.custom_errors import CampaignException
from email_campaign_service.common.models.candidate import CandidateEmail
from email_campaign_service.common.tests.conftest import *

from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.email_campaign import EmailCampaignSend, EmailCampaignBlast
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.tests.modules.handy_functions import create_smartlist_with_candidate, send_email_using_amazon_ses


def test_send_campaign_to_invalid_email_address(access_token_first, assign_roles_to_user_first, email_campaign_of_user_first,
                                                candidate_first, user_first, talent_pipeline):
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

        email_campaign_send = EmailCampaignSend(campaign_id=campaign.id,
                                                candidate_id=candidate_ids[0],
                                                sent_datetime=datetime.now(),
                                                blast_id=email_campaign_blast.id)
        EmailCampaignSend.save(email_campaign_send)
        invalid_email = 'invalid_' + fake.uuid4() + '@gmail.com'
        email = CandidateEmail.query.filter_by(candidate_id=candidate_ids[0]).first()
        email.update(address=invalid_email)
        db.session.commit()
        send_email_using_amazon_ses(campaign, email, candidate_ids[0], email_campaign_blast.id)
        # TODO: Basit is working on removing sleep and using polling. Impliment polling when code is in develop.
        time.sleep(30)
        db.session.commit()
        email = CandidateEmail.query.filter_by(candidate_id=candidate_ids[0]).first()
        assert email.is_bounced is True
        campaign_blasts = campaign.blasts.all()
        assert len(campaign_blasts) == 1
        campaign_blast = campaign_blasts[0]
        assert campaign_blast.bounces == 1

        # Since there is no candidate associated with campaign with valid email, so we will get 400 status while
        # sending this campaign
        response = requests.post(
            EmailCampaignUrl.SEND % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == 400
        response = response.json()
        assert response['error']['code'] == CampaignException.NO_VALID_CANDIDATE_FOUND


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
        # create candidate
        email_campaign_blast, smartlist_id, candidate_ids = create_campaign_data(access_token_first, campaign.id,
                                                                                 talent_pipeline, candidate_count=count)
        # Update first candidate's email to a valid email, i.e. testing email.
        valid_email = 'gettalentmailtest@gmail.com'
        email = CandidateEmail.query.filter_by(candidate_id=candidate_ids[0]).first()
        email.update(address=valid_email)
        # Update second candidate's email to an invalid email, so we can test email bounce
        invalid_email = 'invalid_' + fake.uuid4() + '@gmail.com'
        email = CandidateEmail.query.filter_by(candidate_id=candidate_ids[1]).first()
        email.update(address=invalid_email)
        db.session.commit()

        for index in range(count):
            email = CandidateEmail.query.filter_by(candidate_id=candidate_ids[index]).first()
            send_email_using_amazon_ses(campaign, email, candidate_ids[index], email_campaign_blast.id)

        # TODO: Add polling when Basit's  code for polling is in develop
        time.sleep(30)
        db.session.commit()
        email = CandidateEmail.query.filter_by(candidate_id=candidate_ids[0]).first()
        # first candidate has a valid email. So it is not bounced
        assert email.is_bounced is False

        email = CandidateEmail.query.filter_by(candidate_id=candidate_ids[1]).first()
        # second candidate has an invalid email. So it is bounced
        assert email.is_bounced is True

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
            EmailCampaignUrl.SEND % campaign.id, headers=dict(Authorization='Bearer %s' % access_token_first))
        assert response.status_code == 200
        time.sleep(30)

        db.session.commit()
        campaign_blasts = campaign.blasts.all()
        assert len(campaign_blasts) == 2

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
    smartlist_id, candidate_ids = create_smartlist_with_candidate(access_token,
                                                                  talent_pipeline,
                                                                  emails_list=True,
                                                                  count=candidate_count)

    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign_id)
    email_campaign_blast = EmailCampaignBlast(campaign_id=campaign_id,
                                              sent_datetime=datetime.now())
    EmailCampaignBlast.save(email_campaign_blast)
    return email_campaign_blast, smartlist_id, candidate_ids
