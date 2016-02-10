import json
import uuid
import imaplib
import time
import email
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import *
from email_campaign_service.common.routes import EmailCampaignUrl, CandidatePoolApiUrl
from email_campaign_service.common.utils.candidate_service_calls import create_candidates_from_candidate_api
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import create_smartlist_from_api
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.models.email_marketing import EmailCampaign
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.utils.handy_functions import add_role_to_test_user

__author__ = 'jitesh'


def test_get_all_email_campaigns(user_first, access_token_first, talent_pool, talent_pipeline):
    """
    Test GET API of email_campaigns for getting all campaigns
    """
    # create candidate
    smartlist_id, candidate_ids = create_smartlist_with_candidate(user_first, access_token_first, talent_pool)
    email_campaign_name = fake.name()
    reply_to_name = fake.name()
    email_campaign_subject = fake.sentence()
    campaign_body_html = "<html><body>Email campaign test</body></html>"
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
    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                      email_campaign_id=email_campaign.id)
    # Test GET api of email campaign
    response = requests.get(url=EmailCampaignUrl.CAMPAIGNS,
                 headers={'Authorization': 'Bearer %s' % access_token_first})
    assert response.status_code == 200
    resp = response.json()
    assert 'email_campaigns' in resp
    email_campaigns = resp['email_campaigns']
    for email_campaign in email_campaigns:
        assert 'id' in email_campaign
        assert resp['email_campaigns']

    # Test GET api of email campaign
    response = requests.get(url=EmailCampaignUrl.CAMPAIGNS,
                 headers={'Authorization': 'Bearer %s' % access_token_first})
    assert response.status_code == 200
    resp = response.json()
    assert 'email_campaigns' in resp
    email_campaigns = resp['email_campaigns']
    for email_campaign in email_campaigns:
        assert 'id' in email_campaign
        assert resp['email_campaigns']

    # Test GET api of talent-pipelines/:id/campaigns
    response = requests.get(url=CandidatePoolApiUrl.TALENT_PIPELINE_CAMPAIGN % talent_pipeline.id,
                            headers={'Authorization': 'Bearer %s' % access_token_first})
    assert response.status_code == 200
    resp = response.json()
    print "Response of talent pipelines/candidates call: ", resp
    assert 'email_campaigns' in resp



def create_smartlist_with_candidate(user, access_token, talent_pool):
    # create candidate
    data = FakeCandidatesData.create(talent_pool=talent_pool, count=1)
    add_role_to_test_user(user, ['CAN_ADD_CANDIDATES', 'CAN_GET_CANDIDATES'])
    candidate_ids = create_candidates_from_candidate_api(access_token, data, return_candidate_ids_only=True)
    smartlist_data = {'name': fake.word(),
                      'candidate_ids': candidate_ids}
    smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
    smartlist_id = smartlists['smartlist']['id']
    return smartlist_id, candidate_ids


def test_create_email_campaign(user_first, access_token_first, talent_pool):
    email_campaign_name = fake.name()
    email_subject = uuid.uuid4().__str__()[0:8] + '-test_create_email_campaign'
    email_from = fake.name()
    email_reply_to = fake.safe_email()
    email_body_text = fake.sentence()
    email_body_html = "<html><body><h1>%s</h1></body></html>" % email_body_text
    smartlist_id, candidate_ids = create_smartlist_with_candidate(user_first, access_token_first, talent_pool)
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
    # add_role_to_test_user(user_first, ['CAN_GET_CANDIDATES'])
    r = requests.post(
        url=EmailCampaignUrl.CAMPAIGNS,
        data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % access_token_first,
                 'content-type': 'application/json'}
    )
    assert r.status_code == 201
    resp_object = r.json()
    assert 'campaign' in resp_object
    # Wait for 10 seconds for scheduler to execute it and then assert mail.
    time.sleep(10)
    # Check for email received.
    assert_mail(email_subject)


def test_create_email_campaign_whitespace_campaign_name(user_first, access_token_first, talent_pool):
    email_campaign_name = '       '
    email_subject = uuid.uuid4().__str__()[0:8] + '-test_create_email_campaign_whitespace_campaign_name'
    email_from = 'no-reply@gettalent.com'
    email_reply_to = fake.safe_email()
    email_body_text = fake.sentence()
    email_body_html = "<html><body><h1>%s</h1></body></html>" % email_body_text
    smartlist_id, candidate_ids = create_smartlist_with_candidate(user_first, access_token_first, talent_pool)
    data = {'email_campaign_name': email_campaign_name,
            'email_subject': email_subject,
            'email_from': email_from,
            'email_reply_to': email_reply_to,
            'email_body_html': email_body_html,
            'email_body_text': email_body_text,
            'list_ids': [smartlist_id]
            }
    r = requests.post(
        url=EmailCampaignUrl.CAMPAIGNS,
        data=json.dumps(data),
        headers={'Authorization': 'Bearer %s' % access_token_first,
                 'content-type': 'application/json'}
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
    header_subject = '(HEADER Subject "%s")' % email_subject
    # Wait for 10 seconds then start the loop for 60 seconds
    time.sleep(10)
    while True:
        delta = time.time() - start
        mail.select("inbox")  # connect to inbox.
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
