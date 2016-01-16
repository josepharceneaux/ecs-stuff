import json
import uuid
import imaplib
import time
import email

from email_campaign_service.common.tests.conftest import *
from email_campaign_service.common.tests.sample_data import generate_single_candidate_data
from email_campaign_service.common.models.smartlist import Smartlist, SmartlistCandidate
from email_campaign_service.common.routes import CandidateApiUrl
__author__ = 'jitesh'

EMAIL_CAMPAIGN_URI = "http://127.0.0.1:8014/email_campaign"
CANDIDATE_SERVICE_BASE_URI = "http://127.0.0.1:8005/v1/"
CREATE_CANDIDATE_URI = CandidateApiUrl.CANDIDATES
CREATE_SMARTLIST_URI = CANDIDATE_SERVICE_BASE_URI + "smartlist"


def test_create_email_campaign(sample_user, user_auth):
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    email_campaign_name = fake.name()
    email_subject = uuid.uuid4().__str__()[0:8] + ' test_email_campaign_api::test_create_email_campaign'
    email_from = 'no-reply@gettalent.com'
    email_reply_to = fake.safe_email()
    email_body_text = fake.sentence()
    email_body_html = "<html><body><h1>%s</h1></body></html>" % email_body_text
    list_ids = create_dumblist(auth_token_row)
    data = {'email_campaign_name': email_campaign_name,
            'email_subject': email_subject,
            'email_from': email_from,
            'email_reply_to': email_reply_to,
            'email_body_html': email_body_html,
            'email_body_text': email_body_text,
            'list_ids': list_ids
            }
    r = requests.post(
        url=EMAIL_CAMPAIGN_URI,
        data=data,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()
    assert 'campaign' in resp_object
    assert_mail(email_subject)

def test_create_email_campaign_invalid_campaign_name(sample_user, user_auth):
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    email_campaign_name = '       '
    email_subject = uuid.uuid4().__str__()[0:8] + ' test_email_campaign_api::test_create_email_campaign'
    email_from = 'no-reply@gettalent.com'
    email_reply_to = fake.safe_email()
    email_body_text = fake.sentence()
    email_body_html = "<html><body><h1>%s</h1></body></html>" % email_body_text
    list_ids = create_dumblist(auth_token_row)
    data = {'email_campaign_name': email_campaign_name,
            'email_subject': email_subject,
            'email_from': email_from,
            'email_reply_to': email_reply_to,
            'email_body_html': email_body_html,
            'email_body_text': email_body_text,
            'list_ids': list_ids
            }
    r = requests.post(
        url=EMAIL_CAMPAIGN_URI,
        data=data,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()
    assert 'error' in resp_object
    assert resp_object['error']['message'] == 'email_campaign_name is required'

def create_candidate(auth_token_row):
    r = requests.post(
        url=CREATE_CANDIDATE_URI,
        data=json.dumps(generate_single_candidate_data()),
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()
    return resp_object['candidates'][0]['id']  # return created candidate id


def create_dumblist(auth_token_row):
    # auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    # data = {}
    # r = requests.post(
    #     url=CREATE_SMARTLIST_URI,
    #     data=data,
    #     headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    # )
    # resp_object = r.json()
    # TODO: find out the right way for creating smartlist.
    # create candidate
    candidate_id = create_candidate(auth_token_row)
    # Create smartlist
    list_obj = Smartlist(name=fake.word(), user_id=auth_token_row['user_id'])
    db.session.add(list_obj)
    db.session.commit()
    smartlist_candidate = SmartlistCandidate(smart_list_id=list_obj.id, candidate_id=candidate_id)
    db.session.add(smartlist_candidate)
    db.session.commit()
    return list_obj.id



def create_smartlist(sample_user, user_auth, search_params):
    auth_token_row = user_auth.get_auth_token(sample_user, get_bearer_token=True)
    data = {}
    r = requests.post(
        url=CREATE_SMARTLIST_URI,
        data=data,
        headers={'Authorization': 'Bearer %s' % auth_token_row['access_token']}
    )
    resp_object = r.json()


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
