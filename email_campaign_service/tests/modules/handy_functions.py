"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Um-I-Hani, QC-Technologies, <haniqadri.qc@gmail.com>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    Here are the helper functions used in tests of email-campaign-service
"""

# Standard Imports
import re
import json
import uuid
import email
import imaplib
import datetime

# Third Party
import requests
from redo import retry
from requests import codes

# Application Specific
from __init__ import ALL_EMAIL_CAMPAIGN_FIELDS
from email_campaign_service.common.models.db import db
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
                                                                 EmailClient, EmailCampaignSend)
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.utils.handy_functions import define_and_send_request
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers

__author__ = 'basit'

TEST_EMAIL_ID = 'test.gettalent@gmail.com'
ON = 1  # Global variable for comparing value of is_immutable in the functions to avoid hard-coding 1
EMAIL_TEMPLATE_BODY = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
                      '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
                      '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test campaign mail testing through ' \
                      'script</p>\r\n</body>\r\n</html>\r\n'


class EmailCampaignTypes(object):
    """
    This defines 2 types of email-campaigns
    """
    WITH_CLIENT = 'with_client'
    WITHOUT_CLIENT = 'without_client'


def create_email_campaign(user):
    """
    This creates an email campaign for given user
    """
    email_campaign = EmailCampaign(name=fake.name(),
                                   user_id=user.id,
                                   is_hidden=0,
                                   subject=uuid.uuid4().__str__()[0:8] + ' It is a test campaign',
                                   description=fake.paragraph(),
                                   _from=TEST_EMAIL_ID,
                                   reply_to=TEST_EMAIL_ID,
                                   body_html="<html><body>Email campaign test</body></html>",
                                   body_text="Email campaign test"
                                   )
    EmailCampaign.save(email_campaign)
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


def create_smartlist_with_given_email_candidate(access_token, campaign,
                                                talent_pipeline, emails_list=True,
                                                count=1, emails=None):
    """
    This creates candidate(s) as specified by the count, using the email list provided by the user
    and assign it to a smartlist.
    Finally it returns campaign object
    """
    # create candidates data
    data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool,
                                     emails_list=emails_list, count=count)

    if emails and emails_list:
        for index, candidate in enumerate(data['candidates']):
            candidate['emails'] = emails[index]

    smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token,
                                                                            talent_pipeline,
                                                                            data=data)
    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign.id)

    return campaign


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
            if email_campaign_dict['id'] == referenced_campaign.id:
                found = True
        assert found


def get_campaign_or_campaigns(access_token, campaign_id=None, fields=None, pagination_query=None):
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
    if pagination_query:
        url = url + pagination_query

    params = {'fields': ','.join(fields)} if fields else {}
    response = requests.get(url=url,
                            params=params,
                            headers={'Authorization': 'Bearer %s' % access_token})
    assert response.status_code == requests.codes.OK
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
                            password=app.config[TalentConfigKeys.GT_GMAIL_PASSWORD], delete_email=True):
    """
    Asserts that the user received the email in his inbox which has the given subject.
    It then deletes the email from the inbox.
    :param string subject:       Email subject
    :param string username: Username for login
    :param string password: Password to login to given account
    :param bool delete_email: If True, emails with given subject will be delete from given account
    """
    mail_connection = get_mail_connection(username, password)
    print "Checking for Email with subject: %s" % subject
    mail_connection.select("inbox")  # connect to inbox.
    # search the inbox for given email-subject
    search_criteria = '(SUBJECT "%s")' % subject
    result, [msg_ids] = mail_connection.search(None, search_criteria)
    assert msg_ids, "Email with subject %s was not found at time: %s." % (subject, str(datetime.datetime.utcnow()))
    print "Email(s) found with subject: %s" % subject
    if delete_email:
        # This is kind of finalizer which removes email from inbox. It shouldn't affect our test. So we are not
        # raising it.
        try:
            msg_ids = ','.join(msg_ids.split(' '))
            # Change the Deleted flag to delete the email from Inbox
            mail_connection.store(msg_ids, '+FLAGS', r'(\Deleted)')
            status, response = mail_connection.expunge()
            assert status == 'OK'
            print "Email(s) deleted with subject: %s" % subject
            mail_connection.close()
            mail_connection.logout()
        except imaplib.IMAP4_SSL.error as error:
            logger.exception(error.message)
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
    mail_connection.select("inbox")  # connect to inbox.
    msg_ids = [msg_id for msg_id in msg_ids.split()]
    body = []
    for num in msg_ids:
        typ, data = mail_connection.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        # converts byte literal to string removing b''
        email_message = email.message_from_string(raw_email_string)
        # this will loop through all the available multiparts in mail
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":  # ignore attachments/html
                body.append(part.get_payload(decode=True))
    return body


def assert_campaign_send(response, campaign, user, expected_count=1, email_client=False, expected_status=codes.OK,
                         abort_time_for_sends=300, delete_email=True):
    """
    This assert that campaign has successfully been sent to candidates and campaign blasts and
    sends have been updated as expected. It then checks the source URL is correctly formed or
    in database table "url_conversion".
    """
    msg_ids = ''
    assert response.status_code == expected_status
    assert response.json()
    if not email_client:
        json_resp = response.json()
        assert str(campaign.id) in json_resp['message']
    # Need to add this as processing of POST request runs on Celery
    CampaignsTestsHelpers.assert_campaign_blasts(campaign, 1, timeout=abort_time_for_sends)

    # assert on sends
    CampaignsTestsHelpers.assert_blast_sends(campaign, expected_count,
                                             abort_time_for_sends=abort_time_for_sends)
    campaign_sends = campaign.sends.all()
    assert len(campaign_sends) == expected_count
    sends_url_conversions = []
    # assert on activity of individual campaign sends
    for campaign_send in campaign_sends:
        # Get "email_campaign_send_url_conversion" records
        sends_url_conversions.extend(campaign_send.url_conversions)
        if not email_client:
            assert campaign_send.ses_message_id
            assert campaign_send.ses_request_id
            CampaignsTestsHelpers.assert_for_activity(user.id, Activity.MessageIds.CAMPAIGN_EMAIL_SEND,
                                                      campaign_send.id)
    if campaign_sends:
        # assert on activity for whole campaign send
        CampaignsTestsHelpers.assert_for_activity(user.id, Activity.MessageIds.CAMPAIGN_SEND, campaign.id)
        if not email_client:
            msg_ids = retry(assert_and_delete_email, sleeptime=5, attempts=80, sleepscale=1,
                            args=(campaign.subject,), kwargs=dict(delete_email=delete_email),
                            retry_exceptions=(AssertionError, imaplib.IMAP4_SSL.error))

            assert msg_ids, "Email with subject %s was not found at time: %s." % (campaign.subject,
                                                                      str(datetime.datetime.utcnow()))
    # For each url_conversion record we assert that source_url is saved correctly
    for send_url_conversion in sends_url_conversions:
        # get URL conversion record from database table 'url_conversion' and delete it
        # delete url_conversion record
        assert str(send_url_conversion.url_conversion.id) in send_url_conversion.url_conversion.source_url
        UrlConversion.delete(send_url_conversion.url_conversion)
    return msg_ids


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


def get_template_folder(headers):
    """
    Function will create and retrieve template folder
    :type headers: dict
    :return: template_folder_id, template_folder_name
    :rtype: tuple[int, str]
    """
    template_folder_name = 'test_template_folder_%i' % datetime.datetime.now().microsecond

    data = {'name': template_folder_name,
            'is_immutable': ON}
    response = requests.post(url=EmailCampaignApiUrl.TEMPLATE_FOLDERS, data=json.dumps(data),
                             headers=headers)
    assert response.status_code == requests.codes.CREATED
    response_obj = response.json()
    template_folder_id = response_obj["id"]
    return template_folder_id, template_folder_name


def data_to_create_email_template(headers, template_owner, body_html='', body_text=''):
    """
    This returns data to create an email-template with params provided
    :rtype: dict
    """
    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(headers)
    template_name = 'test_email_template_%i' % datetime.datetime.utcnow().microsecond
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


def add_email_template(headers, template_owner):
    """
    This function will create email template with valid data.
    :rtype: dict
    """
    data = data_to_create_email_template(headers, template_owner, EMAIL_TEMPLATE_BODY)
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


def create_email_campaign_via_api(access_token, data, is_json=True):
    """
    This function makes HTTP POST call on /v1/email-campaigns to create
    an email-campaign. It then returns the response from email-campaigns API.
    :param access_token: access token of user
    :param data: data required for creation of campaign
    :param is_json: If True, it will take dumps of data to be sent in POST call. Otherwise it
                    will send data as it is.
    :return: response of API call
    """
    if is_json:
        data = json.dumps(data)
    response = requests.post(
        url=EmailCampaignApiUrl.CAMPAIGNS,
        data=data,
        headers={'Authorization': 'Bearer %s' % access_token,
                 'content-type': 'application/json'}
    )
    return response


def create_data_for_campaign_creation(access_token, talent_pipeline, subject,
                                      campaign_name=fake.name(), assert_candidates=True, create_smartlist=True):
    """
    This function returns the required data to create an email campaign
    """
    smartlist_id = ''
    email_from = 'no-reply@gettalent.com'
    reply_to = fake.safe_email()
    body_text = fake.sentence()
    description = fake.paragraph()
    body_html = "<html><body><h1>%s</h1></body></html>" % body_text
    if create_smartlist:
        smartlist_id, _ = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token,
                                                                                talent_pipeline,
                                                                                emails_list=True,
                                                                                assert_candidates=assert_candidates)
    return {'name': campaign_name,
            'subject': subject,
            'description': description,
            'from': email_from,
            'reply_to': reply_to,
            'body_html': body_html,
            'body_text': body_text,
            'frequency_id': Frequency.ONCE,
            'list_ids': [smartlist_id] if smartlist_id else []
            }


def send_campaign_email_to_candidate(campaign, email, candidate_id, sent_datetime=None, blast_id=None):
    """
    This function will create a campaign send object and then it will send the email to given email address.
    :param EmailCampaign campaign: EmailCampaign object
    :param CandidateEmail email: CandidateEmail object
    :param (int | long) candidate_id: candidate unique id
    :param (datetime.datetime | None) sent_datetime: Campaign send time to be set in campaign send object.
    :param (None| int | long) blast_id: campaign blast id
    """
    # Create an campaign send object
    email_campaign_send = EmailCampaignSend(campaign_id=campaign.id,
                                            candidate_id=candidate_id,
                                            sent_datetime=sent_datetime if sent_datetime
                                            else datetime.datetime.utcnow(),
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
