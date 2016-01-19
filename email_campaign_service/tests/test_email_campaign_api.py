import json
import uuid
import imaplib
import time
import email
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import *
from email_campaign_service.common.tests.sample_data import generate_single_candidate_data
from email_campaign_service.common.models.smartlist import Smartlist, SmartlistCandidate
from email_campaign_service.common.routes import CandidateApiUrl, EmailCampaignUrl, CandidatePoolApiUrl
from email_campaign_service.common.utils.candidate_service_calls import create_candidates_from_candidate_api
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import create_smartlist_from_api
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.models.email_marketing import EmailCampaign
from email_campaign_service.modules.email_marketing import create_email_campaign_smart_lists

__author__ = 'jitesh'

# EMAIL_CAMPAIGN_URI = "http://127.0.0.1:8014/email_campaign"
# CANDIDATE_SERVICE_BASE_URI = "http://127.0.0.1:8005/v1/"
# CREATE_CANDIDATE_URI = CandidateApiUrl.CANDIDATES
# CREATE_SMARTLIST_URI = CANDIDATE_SERVICE_BASE_URI + "smartlist"


def test_get_all_email_campaigns(user_first, access_token_first):
    """

    :param sample_user:
    :param user_auth:
    :return:
    """
    # create candidate
    data = FakeCandidatesData.create(count=5)
    candidate_ids = create_candidates_from_candidate_api(access_token_first, data, return_candidate_ids_only=True)
    name = fake.word()
    smartlist_data = {'name': name,
                      'candidate_ids': candidate_ids}
    smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token_first)
    smartlist_id = smartlists['smartlist']['id']
    email_campaign_name = fake.name()
    reply_to_name = fake.name()
    email_campaign_subject= fake.sentence()
    campaign_body_html="<html><body>Email campaign test</body></html>"
    email_campaign = EmailCampaign(name=email_campaign_name,
                                   user_id=user_first.id,
                                   is_hidden=0,
                                   email_subject=email_campaign_subject,
                                   email_from=fake.safe_email(),
                                   email_reply_to=reply_to_name,
                                   email_body_html=campaign_body_html,
                                   email_body_text="Email campaign test"
                                   )
    db.session.add(email_campaign)
    db.session.commit()
    create_email_campaign_smart_lists(smart_list_ids=[smartlist_id],
                                      email_campaign_id=email_campaign.id)
    # Test GET api of email campaign
    response = requests.get(url=EmailCampaignUrl.EMAIL_CAMPAIGNS,
                 headers={'Authorization': 'Bearer %s' % access_token_first})
    assert response.status_code == 200
    resp = response.json()
    assert 'email_campaigns' in resp
    email_campaigns = resp['email_campaigns']
    for email_campaign in email_campaigns:
        assert 'id' in email_campaign
        assert resp['email_campaigns']


def create_smartlist(access_token):
    # create candidate
    data = FakeCandidatesData.create(count=1)
    candidate_ids = create_candidates_from_candidate_api(access_token, data, return_candidate_ids_only=True)
    smartlist_data = {'name': fake.word(),
                      'candidate_ids': candidate_ids}
    smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
    smartlist_id = smartlists['smartlist']['id']
    return smartlist_id


def _test_create_email_campaign(user_first, access_token_first):
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    smartlist_id = create_smartlist()
    email_campaign_name = fake.name()
    email_subject = uuid.uuid4().__str__()[0:8] + ' test_email_campaign_api::test_create_email_campaign'
    email_from = fake.name()
    email_reply_to = fake.safe_email()
    email_body_text = fake.sentence()
    email_body_html = "<html><body><h1>%s</h1></body></html>" % email_body_text
    smartlist_id = create_smartlist(auth_token_row)
    data = {
        "email_campaign_name": email_campaign_name,
        "email_subject": email_subject,
        "email_from": email_from,
        "email_reply_to": email_reply_to,
        "email_body_html": email_body_html,
        "email_body_text": email_body_text,
        "list_ids": [smartlist_id],
        # "email_client_id": 1
    }
    r = requests.post(
        url=EmailCampaignUrl.EMAIL_CAMPAIGNS,
        data=data,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()
    assert 'campaign' in resp_object
    # Wait for 10 seconds for scheduler to execute it and then assert mail.
    assert_mail(email_subject)


def _test_create_email_campaign_invalid_campaign_name(sample_user, user_auth):
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    email_campaign_name = '       '
    email_subject = uuid.uuid4().__str__()[0:8] + ' test_email_campaign_api::test_create_email_campaign'
    email_from = 'no-reply@gettalent.com'
    email_reply_to = fake.safe_email()
    email_body_text = fake.sentence()
    email_body_html = "<html><body><h1>%s</h1></body></html>" % email_body_text
    list_ids = create_smartlist(auth_token_row)
    data = {'email_campaign_name': email_campaign_name,
            'email_subject': email_subject,
            'email_from': email_from,
            'email_reply_to': email_reply_to,
            'email_body_html': email_body_html,
            'email_body_text': email_body_text,
            'list_ids': list_ids
            }
    r = requests.post(
        url=EmailCampaignUrl.EMAIL_CAMPAIGNS,
        data=data,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()
    assert 'error' in resp_object
    assert resp_object['error']['message'] == 'email_campaign_name is required'


# def test_create_email_campaign_with_email_client(user_first, access_token_first):
#

def assert_mail(email_subject):
    """
    Asserts that the user received the email in his inbox which has the email_subject as subject,


    :param email_subject:       Email subject
    :return:
    """
    abort_after = 60
    start = time.time()
    mail_found = False
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login('gettalentmailtest@gmail.com', 'GetTalent@1234')
    # mail.list()  # Out: list of "folders" aka labels in gmail.
    print "Check for mail with subject: %s" % email_subject
    mail.select("inbox")  # connect to inbox.
    header_subject = '(HEADER Subject "%s")' % email_subject

    while True:
        delta = time.time() - start

        result, data = mail.uid('search', None, header_subject)

        for latest_email_uid in data[0].split():
            result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')
            raw_email = data[0][1]

            email_message = email.message_from_string(raw_email)

            raw_mail_subject_ = ''.join(email_message['Subject'].split())
            test_email_subject = ''.join(email_subject.split())
            if raw_mail_subject_ == test_email_subject:
                mail_found = True
                break

        if mail_found:
            break

        if delta >= abort_after:
            break

    assert mail_found, "Mail with subject %s was not found." % email_subject
