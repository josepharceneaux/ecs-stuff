"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Um-I-Hani, QC-Technologies, <haniqadri.qc@gmail.com>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    Here are the helper functions used in tests of email-campaign-service
"""

# Standard Imports
import re
import json
import email
import imaplib
from datetime import datetime, timedelta

# Third Party
import requests
from requests import codes

# Application Specific
from __init__ import ALL_EMAIL_CAMPAIGN_FIELDS
from email_campaign_service.common.models.db import db
from email_campaign_service.common.models.user import Domain
from email_campaign_service.email_campaign_app import app, logger
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.models.misc import (Activity,
                                                       UrlConversion,
                                                       Frequency)
from email_campaign_service.common.routes import (EmailCampaignApiUrl,
                                                  CandidatePoolApiUrl)
from email_campaign_service.common.utils.amazon_ses import (send_email,
                                                            get_default_email_info)
from email_campaign_service.common.models.email_campaign import (EmailCampaign,
                                                                 EmailClient, EmailCampaignSend,
                                                                 EmailClientCredentials, EmailCampaignBlast)
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.utils.handy_functions import define_and_send_request
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.utils.datetime_utils import DatetimeUtils
from email_campaign_service.modules.utils import (DEFAULT_FIRST_NAME_MERGETAG, DEFAULT_PREFERENCES_URL_MERGETAG,
                                                  DEFAULT_LAST_NAME_MERGETAG, DEFAULT_USER_NAME_MERGETAG)
from email_campaign_service.common.campaign_services.tests.modules.email_campaign_helper_functions import \
    create_email_campaign_via_api, create_scheduled_email_campaign_data

__author__ = 'basit'

TEST_EMAIL_ID = 'test.gettalent@gmail.com'
ON = 1  # Global variable for comparing value of is_immutable in the functions to avoid hard-coding 1
EMAIL_TEMPLATE_BODY = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                      '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
                      '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test campaign mail testing through ' \
                      'script</p>\r\n</body>\r\n</html>\r\n'
EMAIL_CAMPAIGN_OPTIONAL_PARAMETERS = [{'from': fake.safe_email()}, {'from': fake.safe_email(),
                                                                    'reply_to': fake.safe_email()},
                                      {'from': fake.safe_email(),
                                       'reply_to': fake.safe_email(), 'body_text': fake.sentence()},
                                      {'from': fake.safe_email(), 'reply_to': fake.safe_email(),
                                       'description': fake.sentence(), 'body_text': fake.sentence(),
                                       'start_datetime': DatetimeUtils.to_utc_str(datetime.utcnow()
                                                                                  + timedelta(minutes=20))},
                                      {'from': fake.safe_email(), 'reply_to': fake.safe_email(),
                                       'body_text': fake.sentence(), 'start_datetime': DatetimeUtils.to_utc_str(
                                          datetime.utcnow() + timedelta(minutes=20)),
                                       'end_datetime': DatetimeUtils.to_utc_str(datetime.utcnow()
                                                                                + timedelta(minutes=40))}]

SPECIAL_CHARACTERS = '!@#$%^&*()_+'
TEST_MAIL_DATA = {
    "subject": "Test Email-%s-%s" % (fake.uuid4()[0:8], SPECIAL_CHARACTERS),
    "from": fake.name(),
    "body_html": "<html><body><h1>Welcome to email campaign service "
                 "<a href=https://www.github.com>Github</a></h1></body></html>",
    "body_text": fake.sentence() + fake.uuid4() + SPECIAL_CHARACTERS,
    "email_address_list": [app.config[TalentConfigKeys.GT_GMAIL_ID]],
    "reply_to": fake.safe_email()
}


class EmailCampaignTypes(object):
    """
    This defines 2 types of email-campaigns
    """
    WITH_CLIENT = 'with_client'
    WITHOUT_CLIENT = 'without_client'


def create_email_campaign_in_db(user_id, add_subject=True):
    """
    This creates an email campaign for given user
    """
    email_campaign = EmailCampaign(name=fake.name(), user_id=user_id, is_hidden=0,
                                   subject='{}-{}'.format('Test campaign created in db', fake.uuid4()[0:8])
                                   if add_subject else '',
                                   description=fake.paragraph(), _from=TEST_EMAIL_ID,
                                   reply_to=TEST_EMAIL_ID, body_text=fake.sentence(),
                                   body_html="<html><body><a href=%s>Email campaign test</a></body></html>"
                                             % fake.url(),
                                   )
    EmailCampaign.save(email_campaign)
    return email_campaign


def create_and_get_email_campaign(campaign_data, access_token):
    """
    This creates an email-campaign using API and returns EmailCampaign object from database.
    """
    response = create_email_campaign_via_api(access_token, campaign_data)
    assert response.status_code == codes.CREATED, response.text
    resp_object = response.json()
    assert 'campaign' in resp_object
    campaign_id = resp_object['campaign']['id']
    assert campaign_id > 0, 'Expecting positive campaign_id'
    db.session.commit()
    campaign = EmailCampaign.get_by_id(campaign_id)
    return campaign


def create_email_campaign_with_merge_tags(smartlist_id=None, access_token=None, add_preference_url=True,
                                          in_db_only=False, user_id=None):
    """
    This function creates an email-campaign containing merge tags.
    """
    if in_db_only:
        email_campaign = create_email_campaign_in_db(user_id, add_subject=False)
    else:
        campaign_data = create_scheduled_email_campaign_data(smartlist_id=smartlist_id)
        email_campaign = create_and_get_email_campaign(campaign_data, access_token)
    # Update email-campaign's body text
    starting_string = 'Hello %s %s' % (DEFAULT_FIRST_NAME_MERGETAG, DEFAULT_LAST_NAME_MERGETAG)
    ending_string = ' Thanks, %s' % DEFAULT_USER_NAME_MERGETAG
    email_campaign.update(subject=starting_string + email_campaign.subject)
    if add_preference_url:
        starting_string += ', Unsubscribe URL is:%s' % DEFAULT_PREFERENCES_URL_MERGETAG
    email_campaign.update(body_text=starting_string + email_campaign.body_text + ending_string,
                          body_html=starting_string + email_campaign.body_html + ending_string)

    return email_campaign


def create_email_campaign_smartlist(access_token, talent_pipeline, campaign, emails_list=True, count=1,
                                    assert_candidates=True):
    """
    This associates smartlist ids with given campaign
    """
    # create candidate
    smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token, talent_pipeline,
                                                                            count=count, emails_list=emails_list,
                                                                            assert_candidates=assert_candidates)
    create_email_campaign_smartlists(smartlist_ids=[smartlist_id], email_campaign_id=campaign.id)
    return campaign


def create_smartlist_with_given_email_candidate(access_token, talent_pipeline, emails_list=True, emails=None, count=1):
    """
    This creates candidate(s) as specified by the count, using the email list provided by the user
    and assign it to a smartlist.
    Finally it returns campaign object
    """
    # create candidates data
    data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool, emails_list=emails_list, count=count)
    if emails and emails_list:
        for index, candidate in enumerate(data['candidates']):
            candidate['emails'] = emails[index]
    smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token, talent_pipeline, data=data)
    return smartlist_id


def assert_valid_campaign_get(email_campaign_dict, referenced_campaigns, fields=None):
    """
    This asserts that the campaign we get from GET call has valid values as we have for
    referenced email-campaign.
    :param dict email_campaign_dict: EmailCampaign object as received by GET call
    :param referenced_campaigns: EmailCampaign objects with which we compare the campaign
            we GET in response
    :param list[str] fields: List of fields that the campaign should have, or all of them if None
    """

    # Assert the fields are correct
    expected_email_campaign_fields_set = set(fields or ALL_EMAIL_CAMPAIGN_FIELDS)
    actual_email_campaign_fields_set = set(email_campaign_dict.keys())
    assert expected_email_campaign_fields_set == actual_email_campaign_fields_set, \
        "Response's email campaign fields (%s) should match the expected email campaign fields (%s)" % (
            actual_email_campaign_fields_set, expected_email_campaign_fields_set
        )
    found = False
    # Assert id is correct, if returned by API
    if 'id' in expected_email_campaign_fields_set:
        for referenced_campaign in referenced_campaigns:
            referenced_campaign_id = referenced_campaign.id if hasattr(referenced_campaign, 'id') else \
                referenced_campaign['id']
            if email_campaign_dict['id'] == referenced_campaign_id:
                found = True
        assert found


def get_campaign_or_campaigns(access_token, campaign_id=None, fields=None, query_params=None):
    """
    This makes HTTP GET call on /v1/email-campaigns with given access_token to get
    1) all the campaigns of logged-in user if campaign_id is None
    2) Get campaign object for given campaign_id
    :param list[str] fields: List of EmailCampaign fields to retrieve
    """
    if campaign_id:
        url = EmailCampaignApiUrl.CAMPAIGN % campaign_id
        entity = 'email_campaign'
    else:
        url = EmailCampaignApiUrl.CAMPAIGNS
        entity = 'email_campaigns'
    if query_params:
        url = url + query_params

    params = {'fields': ','.join(fields)} if fields else {}
    response = requests.get(url=url,
                            params=params,
                            headers={'Authorization': 'Bearer %s' % access_token})
    assert response.status_code == requests.codes.OK, response.text
    resp = response.json()
    assert entity in resp
    return resp[entity]


def assert_talent_pipeline_response(talent_pipeline, access_token, fields=None):
    """
    This makes HTTP GET call on candidate_pool_service to get response for given
    talent_pipeline and then asserts if we get an OK response.
    :param list[str] fields:  List of fields each EmailCampaign should have.  If None, will assert on all fields.
    """
    params = {'fields': ','.join(fields)} if fields else {}
    response = requests.get(
        url=CandidatePoolApiUrl.TALENT_PIPELINE_CAMPAIGN % talent_pipeline.id,
        params=params,
        headers={'Authorization': 'Bearer %s' % access_token})
    assert response.status_code == requests.codes.OK
    resp = response.json()
    print "Response JSON: %s" % json.dumps(resp)
    assert 'email_campaigns' in resp, "Response dict should have email_campaigns key"

    # Assert on the existence of email campaign fields
    for email_campaign_dict in resp['email_campaigns']:
        expected_email_campaign_fields_set = set(fields or ALL_EMAIL_CAMPAIGN_FIELDS)
        actual_email_campaign_fields_set = set(email_campaign_dict.keys())
        assert expected_email_campaign_fields_set == actual_email_campaign_fields_set, \
            "Response's email campaign fields should match the expected email campaign fields"


def assert_and_delete_email(subject, username=app.config[TalentConfigKeys.GT_GMAIL_ID],
                            password=app.config[TalentConfigKeys.GT_GMAIL_PASSWORD], delete_email=True,
                            search_criteria=''):
    """
    Asserts that the user received the email in his inbox which has the given subject.
    It then deletes the email from the inbox.
    :param string subject:       Email subject
    :param string username: Username for login
    :param string password: Password to login to given account
    :param bool delete_email: If True, emails with given subject will be delete from given account
    :param string search_criteria: searching criteria
    """
    mail_connection = get_mail_connection(username, password)
    print "Checking for Email with subject: %s" % subject
    mail_connection.select("inbox")  # connect to inbox.
    # search the inbox for given email-subject
    search_criteria = search_criteria or '(SUBJECT "%s")' % subject
    result, [msg_ids] = mail_connection.search(None, search_criteria)
    assert msg_ids, "Email with subject %s was not found at time: %s." % (subject, str(datetime.utcnow()))
    print "Email(s) found with subject: %s" % subject
    if delete_email:
        # This is kind of finalizer which removes email from inbox. It shouldn't affect our test. So we are not
        # raising it.
        delete_emails(mail_connection, msg_ids, subject)
    return msg_ids


def get_mail_connection(username, password):
    """
    This connects with IMAP server and authenticates to email-account.
    """
    try:
        mail_connection = imaplib.IMAP4_SSL('imap.gmail.com')
        if mail_connection.state == 'NONAUTH':  # Makes sure not we are not logged-in already
            mail_connection.login(username, password)
    except imaplib.IMAP4_SSL.error as error:
        print error.message
        raise  # Raise any error raised by IMAP server
    return mail_connection


def fetch_emails(mail_connection, msg_ids):
    """
    This fetches emails with given msg_ids
    """
    assert msg_ids, 'msg_ids cannot be empty'
    mail_connection.select("inbox")  # connect to inbox.
    msg_ids = [msg_id for msg_id in msg_ids.split()]
    body = []
    for num in msg_ids:
        typ, data = mail_connection.fetch(num, '(RFC822)')
        print "Data:%s" % data
        raw_email = data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        # converts byte literal to string removing b''
        email_message = email.message_from_string(raw_email_string)
        # this will loop through all the available multiparts in mail
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":  # ignore attachments/html
                body.append(part.get_payload(decode=True))
    return body


def delete_emails(mail_connection, msg_ids, subject):
    """
    This deletes email(s) with given message ids and subject
    """
    try:
        msg_ids = msg_ids.replace(' ', ',')
        # Change the Deleted flag to delete the email from Inbox
        mail_connection.store(msg_ids, '+FLAGS', r'(\Deleted)')
        status, response = mail_connection.expunge()
        assert status == 'OK'
        print "Email(s) deleted with subject: %s" % subject
        mail_connection.close()
        mail_connection.logout()
    except imaplib.IMAP4_SSL.error as error:
        logger.exception(error.message)


def post_to_email_template_resource(headers, data):
    """
    Function sends a post request to email-templates,
    i.e. EmailTemplate/post()
    It then returns Id of created EmailTemplate
    """
    response = requests.post(url=EmailCampaignApiUrl.TEMPLATES, data=json.dumps(data), headers=headers)
    print response.json()
    return response


def request_to_email_template_resource(access_token, request, email_template_id, data=None):
    """
    Function sends a request to email template resource
    :param access_token: Token for user authorization
    :param request: get, post, patch, delete
    :param email_template_id: Id of email template
    :param data: data in form of dictionary
    """
    url = EmailCampaignApiUrl.TEMPLATE % email_template_id
    return define_and_send_request(access_token, request, url, data)


def create_template_folder(headers):
    """
    Function will create and retrieve template folder
    :type headers: dict
    :return: template_folder_id, template_folder_name
    :rtype: tuple[int, str]
    """
    template_folder_name = 'test_template_folder_{}'.format(datetime.now().microsecond)
    data = {'name': template_folder_name, 'is_immutable': ON}
    response = requests.post(url=EmailCampaignApiUrl.TEMPLATE_FOLDERS, data=json.dumps(data), headers=headers)
    assert response.status_code == requests.codes.CREATED, response.text
    response_obj = response.json()
    template_folder_id = response_obj["id"]
    return template_folder_id, template_folder_name


def data_to_create_email_template(headers, template_owner, body_html='', body_text='', template_folder_id=None):
    """
    This returns data to create an email-template with params provided
    :rtype: dict
    """
    # Get Template Folder Id
    if not template_folder_id:
        template_folder_id, _ = create_template_folder(headers)
    template_name = 'test_email_template_%i' % datetime.utcnow().microsecond
    is_immutable = ON
    data = dict(
        name=template_name,
        template_folder_id=template_folder_id,
        user_id=template_owner.id,
        type=0,
        body_html=body_html,
        body_text=body_text,
        is_immutable=is_immutable
    )
    return data


def update_email_template(email_template_id, request, token, user_id, template_name, body_html,
                          body_text='', folder_id=None, is_immutable=ON):
    """
        Update existing email template fields using values provided by user.
        :param email_template_id: id of email template
        :param request: request object
        :param token: token for authentication
        :param user_id: user's id
        :param template_name: Name of template
        :param body_html: HTML body for email template
        :param body_text: HTML text for email template
        :param folder_id: ID of email template folder
        :param is_immutable: Specify whether the email template is mutable or not
    """
    data = dict(
        name=template_name,
        template_folder_id=folder_id,
        user_id=user_id,
        type=0,
        body_html=body_html,
        body_text=body_text,
        is_immutable=is_immutable
    )

    create_resp = request_to_email_template_resource(token, request, email_template_id, data)
    return create_resp


def add_email_template(headers, template_owner, template_folder_id=None):
    """
    This function will create email template with valid data.
    :rtype: dict
    """
    data = data_to_create_email_template(headers, template_owner, EMAIL_TEMPLATE_BODY,
                                         template_folder_id=template_folder_id)
    response = post_to_email_template_resource(headers, data=data)
    json_response = response.json()
    assert response.status_code == codes.CREATED, response.text
    assert response.json()
    assert 'id' in json_response
    return {"id": json_response['id'],
            "name": data['name'],
            "template_folder_id": data['template_folder_id'],
            "is_immutable": data['is_immutable'],
            "domain_id": template_owner.domain_id}


def send_campaign_email_to_candidate(campaign, email, candidate_id, sent_datetime=None, blast_id=None):
    """
    This function will create a campaign send object and then it will send the email to given email address.
    :param EmailCampaign campaign: EmailCampaign object
    :param CandidateEmail email: CandidateEmail object
    :param (int | long) candidate_id: candidate unique id
    :param (datetime | None) sent_datetime: Campaign send time to be set in campaign send object.
    :param (None| int | long) blast_id: campaign blast id
    """
    # Create an campaign send object
    email_campaign_send = EmailCampaignSend(campaign_id=campaign.id,
                                            candidate_id=candidate_id,
                                            sent_datetime=sent_datetime if sent_datetime
                                            else datetime.utcnow(),
                                            blast_id=blast_id)
    EmailCampaignSend.save(email_campaign_send)
    default_email = get_default_email_info()['email']
    # Send email to given email address with some random text as body.
    email_response = send_email(source='"%s" <%s>' % (campaign._from, default_email),
                                # Emails will be sent from verified email by Amazon SES for respective environment.
                                subject=fake.sentence(),
                                html_body="<html><body>Email campaign test</body></html>",
                                text_body=fake.paragraph(),
                                to_addresses=email.address,
                                reply_address=campaign.reply_to.strip(),
                                body=None,
                                email_format='html' if campaign.body_html else 'text')

    # Get unique request id and message id from response and update campaign send object.
    request_id = email_response[u"SendEmailResponse"][u"ResponseMetadata"][u"RequestId"]
    message_id = email_response[u"SendEmailResponse"][u"SendEmailResult"][u"MessageId"]
    email_campaign_send.update(ses_message_id=message_id, ses_request_id=request_id)
    db.session.commit()


def send_campaign_helper(request, email_campaign, access_token):
    """
    This is a helper function to send campaign with and without email_client_id
    """
    if request.param == EmailCampaignTypes.WITH_CLIENT:
        email_campaign.update(email_client_id=EmailClient.get_id_by_name('Browser'))
    # send campaign
    CampaignsTestsHelpers.send_campaign(EmailCampaignApiUrl.SEND, email_campaign, access_token)
    return email_campaign


def assert_valid_template_object(template_dict, user_id, expected_template_ids, expected_name='', expected_html=''):
    """
    Here we are asserting that response from API /v1/email-templates/:id
    :param dict template_dict: object received from above API endpoints
    :param int|long user_id: Id of user
    :param list[int|long] expected_template_ids: List of email-template ids
    :param string|None expected_name: Expected name of email-template
    :param string|None expected_html: Expected body_html of email-template
    """
    assert template_dict['id'] in expected_template_ids
    if expected_name:
        assert template_dict['name'] == expected_name
    else:
        assert template_dict['name']
    if expected_html:
        assert template_dict['body_html'] == expected_html
    else:
        assert template_dict['body_html']
    assert template_dict['user_id'] == user_id
    assert template_dict['template_folder_id']
    assert template_dict['updated_datetime']
    assert template_dict['is_immutable'] == ON

    # Following fields may have empty values
    assert 'type' in template_dict
    assert 'body_text' in template_dict


def assert_valid_template_folder(template_folder_dict, domain_id, expected_name):
    """
    Here we are asserting that response from API /v1/email-template-folders/:id
    :param dict template_folder_dict: object received from above API endpoints
    :param int|long domain_id: Id of user's domain
    :param string expected_name: Expected name of email-template-folder
    """
    assert template_folder_dict['id']
    assert template_folder_dict['name'] == expected_name
    assert template_folder_dict['domain_id'] == domain_id
    assert template_folder_dict['updated_datetime']
    assert template_folder_dict['is_immutable'] == ON
    # Following fields may have empty values
    assert 'parent_id' in template_folder_dict


def create_data_for_campaign_creation_with_all_parameters(smartlist_id, subject, campaign_name=fake.name()):
    """
    This function returns the all data to create an email campaign
    :param smartlist_id: Id of smartlist
    :param subject: Subject of campaign
    :param campaign_name: Name of campaign
    """
    email_from = 'no-reply@gettalent.com'
    reply_to = fake.safe_email()
    body_text = fake.sentence()
    description = fake.paragraph()
    body_html = "<html><body><h1>%s</h1></body></html>" % body_text
    start_datetime = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(minutes=20))
    end_datetime = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(minutes=40))

    return {'name': campaign_name,
            'from': email_from,
            'reply_to': reply_to,
            'description': description,
            'body_text': body_text,
            'subject': subject,
            'body_html': body_html,
            'frequency_id': Frequency.ONCE,
            'list_ids': [smartlist_id],
            'start_datetime': start_datetime,
            'end_datetime': end_datetime
            }


def assert_and_delete_template_folder(template_folder_id, headers, data=None):
    """
    Here we are asserting the  response code that folder is deleted not.
    :param template_folder_id: Contain id of folder which you want to delete.
    :param data: Contain multiple folder id's to delete more than one folder.
    :param headers: Contain access token and authentication.
    """
    response = requests.delete(url=EmailCampaignApiUrl.TEMPLATE_FOLDER % template_folder_id,
                               data=json.dumps(data), headers=headers)
    assert response.status_code == requests.codes.NO_CONTENT


def data_for_creating_email_clients(key=None):
    """
    This returns data to create email-clients.
    :rtype: list[dict]
    """
    data = {
        EmailClientCredentials.CLIENT_TYPES['outgoing']: [{
            "host": "smtp.gmail.com",
            "port": "465",
            "name": "Gmail",
            "email": app.config[TalentConfigKeys.GT_GMAIL_ID],
            "password": app.config[TalentConfigKeys.GT_GMAIL_PASSWORD],
        }],
        EmailClientCredentials.CLIENT_TYPES['incoming']: [{
            "host": "imap.gmail.com",
            "port": "",
            "name": "Gmail",
            "email": app.config[TalentConfigKeys.GT_GMAIL_ID],
            "password": app.config[TalentConfigKeys.GT_GMAIL_PASSWORD]
        },
            {
                "host": "pop.gmail.com",
                "port": "",
                "name": "Gmail",
                "email": app.config[TalentConfigKeys.GT_GMAIL_ID],
                "password": app.config[TalentConfigKeys.GT_GMAIL_PASSWORD],
            }
        ]
    }
    if key:
        return data[key]
    email_clients_data = []
    for client_type in EmailClientCredentials.CLIENT_TYPES:
        for email_client_data in data_for_creating_email_clients(key=client_type):
            email_clients_data.append(email_client_data)
    return email_clients_data


def assert_email_client_fields(email_client_data, user_id):
    """
    Here we are asserting that response from API GET /v1/email-clients
    :param dict email_client_data: object received from above API endpoint
    :param int|long user_id: Id of user's domain
    """
    assert email_client_data['id']
    assert email_client_data['user_id'] == user_id
    assert email_client_data['host']
    assert 'port' in email_client_data
    assert email_client_data['name']
    assert email_client_data['email']
    assert email_client_data['password']
    assert email_client_data['updated_datetime']


def send_campaign_with_client_id(email_campaign, access_token):
    """
    This make given campaign a client-campaign, sends it and asserts valid response.
    """
    email_campaign.update(email_client_id=EmailClient.get_id_by_name('Browser'))
    response = CampaignsTestsHelpers.send_campaign(EmailCampaignApiUrl.SEND, email_campaign, access_token)
    json_response = response.json()
    assert 'email_campaign_sends' in json_response
    email_campaign_sends = json_response['email_campaign_sends'][0]
    assert 'new_html' in email_campaign_sends
    new_html = email_campaign_sends['new_html']
    matched = re.search(r'&\w+;', new_html)  # check the new_html for escaped HTML characters using regex
    assert not matched  # Fail if HTML escaped characters found, as they render the URL useless
    assert 'new_text' in email_campaign_sends  # Check if there is email text which candidate would see in email
    assert 'email_campaign_id' in email_campaign_sends  # Check if there is email campaign id in response
    assert email_campaign.id == email_campaign_sends['email_campaign_id']  # Check if both IDs are same
    return_value = dict()
    return_value['response'] = response
    return_value['campaign'] = email_campaign
    return return_value


def create_dummy_kaiser_domain():
    """
    This creates a domain with name containing word "Kaiser"
    """
    domain = Domain(name='test_domain_{}_{}'.format('kaiser', fake.uuid4()))
    domain.save()
    return domain.id


def create_campaign_blast_and_sends(campaign_id, candidate_id, number_of_sends):
    """
    This creates records in email_campaign_blast and email_campaign_send for given campaign_id.
    """
    blast = EmailCampaignBlast(campaign_id=campaign_id, sends=number_of_sends)
    EmailCampaignBlast.save(blast)
    for _ in xrange(number_of_sends):
        send = EmailCampaignSend(campaign_id=campaign_id, blast_id=blast.id, candidate_id=candidate_id)
        EmailCampaignSend.save(send)
