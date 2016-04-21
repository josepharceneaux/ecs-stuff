# Standard Imports
import json
import uuid
import time
import imaplib
import datetime

# Third Party
from polling import poll
import requests

# Application Specific
from __init__ import ALL_EMAIL_CAMPAIGN_FIELDS
from email_campaign_service.common.models.db import db
from email_campaign_service.email_campaign_app import (app,
                                                       logger)
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.models.user import DomainRole
from email_campaign_service.common.models.misc import (Activity,
                                                       UrlConversion,
                                                       Frequency)
from email_campaign_service.common.routes import (EmailCampaignUrl,
                                                  CandidatePoolApiUrl)
from email_campaign_service.common.utils.amazon_ses import send_email
from email_campaign_service.common.error_handling import UnprocessableEntity
from email_campaign_service.common.models.email_campaign import (EmailCampaign,
                                                                 EmailClient, EmailCampaignSend)
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.utils.validators import raise_if_not_instance_of
from email_campaign_service.common.utils.handy_functions import (add_role_to_test_user,
                                                                 define_and_send_request)
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import \
    create_smartlist_from_api
from email_campaign_service.common.inter_service_calls.candidate_service_calls import \
    create_candidates_from_candidate_api
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import \
    assert_smartlist_candidates

__author__ = 'basit'


def create_email_campaign(user):
    """
    This creates an email campaign for given user
    """
    email_campaign = EmailCampaign(name=fake.name(),
                                   user_id=user.id,
                                   is_hidden=0,
                                   subject=uuid.uuid4().__str__()[0:8] + ' It is a test campaign',
                                   _from=fake.safe_email(),
                                   reply_to=fake.safe_email(),
                                   body_html="<html><body>Email campaign test</body></html>",
                                   body_text="Email campaign test"
                                   )
    EmailCampaign.save(email_campaign)
    return email_campaign


def assign_roles(user):
    """
    This assign required permission to given user
    :param user:
    """
    add_role_to_test_user(user, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                 DomainRole.Roles.CAN_GET_CANDIDATES])


def create_email_campaign_smartlist(access_token, talent_pipeline, campaign,
                                    emails_list=True, count=1, assert_candidates=True):
    """
    This associates smartlist ids with given campaign
    """
    # create candidate
    smartlist_id, _ = create_smartlist_with_candidate(access_token, talent_pipeline,
                                                      emails_list=emails_list,
                                                      count=count,
                                                      assert_candidates=assert_candidates)

    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign.id)
    return campaign


def create_smartlist_with_candidate(access_token, talent_pipeline, emails_list=True, count=1,
                                    assert_candidates=True, timeout=120, data=None):
    """
    This creates candidate(s) as specified by the count and assign it to a smartlist.
    Finally it returns smartlist_id and candidate_ids.
    """
    if not data:
        # create candidate
        data = FakeCandidatesData.create(talent_pool=talent_pipeline.talent_pool,
                                         emails_list=emails_list, count=count)

    candidate_ids = create_candidates_from_candidate_api(oauth_token=access_token, data=data,
                                                         return_candidate_ids_only=True)
    if assert_candidates:
        time.sleep(10)
    smartlist_data = {'name': fake.word(),
                      'candidate_ids': candidate_ids,
                      'talent_pipeline_id': talent_pipeline.id}

    smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
    smartlist_id = smartlists['smartlist']['id']
    if assert_candidates:
        assert poll(assert_smartlist_candidates, step=3,
                    args=(smartlist_id, len(candidate_ids), access_token), timeout=timeout), \
            'Candidates not found for smartlist(id:%s)' % smartlist_id
        logger.info('%s candidate(s) found for smartlist(id:%s)' % (len(candidate_ids), smartlist_id))
    return smartlist_id, candidate_ids


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

    smartlist_id, _ = create_smartlist_with_candidate(access_token, talent_pipeline, data=data)
    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign.id)

    return campaign


def delete_campaign(campaign):
    """
    This deletes the campaign created during tests from database
    :param campaign: Email campaign object
    """
    try:
        with app.app_context():
            if isinstance(campaign, dict):
                EmailCampaign.delete(campaign['id'])
            else:
                EmailCampaign.delete(campaign.id)
    except Exception:
        pass


def send_campaign(campaign, access_token):
    """
    This function sends the campaign via /v1/email-campaigns/:id/send
    timeout is set to be 20s here. One can modify this by passing required value.
    :param (EmailCampaign) campaign: Email campaign obj
    :param (str) access_token: Auth token to make HTTP request
    """
    raise_if_not_instance_of(campaign, EmailCampaign)
    raise_if_not_instance_of(access_token, basestring)
    # send campaign
    response = requests.post(EmailCampaignUrl.SEND % campaign.id,
                             headers=dict(Authorization='Bearer %s' % access_token))
    assert response.ok
    time.sleep(20)
    blasts = get_blasts_with_polling(campaign)
    if not blasts:
        raise UnprocessableEntity('blasts not found in given time range.')
    return response


def assert_valid_campaign_get(email_campaign_dict, referenced_campaign, fields=None):
    """
    This asserts that the campaign we get from GET call has valid values as we have for
    referenced email-campaign.
    :param dict email_campaign_dict: EmailCampaign object as received by GET call
    :param referenced_campaign: EmailCampaign object by which we compare the campaign
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

    # Assert id is correct, if returned by API
    if 'id' in expected_email_campaign_fields_set:
        assert email_campaign_dict['id'] == referenced_campaign.id


def get_campaign_or_campaigns(access_token, campaign_id=None, fields=None, pagination_query=None):
    """
    This makes HTTP GET call on /v1/email-campaigns with given access_token to get
    1) all the campaigns of logged-in user if campaign_id is None
    2) Get campaign object for given campaign_id
    :param list[str] fields: List of EmailCampaign fields to retrieve
    """
    if campaign_id:
        url = EmailCampaignUrl.CAMPAIGN % campaign_id
        entity = 'email_campaign'
    else:
        url = EmailCampaignUrl.CAMPAIGNS
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


def assert_and_delete_email(subject):
    """
    Asserts that the user received the email in his inbox which has the given subject.
    It then deletes the email from the inbox.
    :param subject:       Email subject
    """
    mail_connection = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        mail_connection.login(app.config[TalentConfigKeys.GT_GMAIL_ID],
                              app.config[TalentConfigKeys.GT_GMAIL_PASSWORD])
    except Exception as error:
        print error.message
        pass  # Maybe already login when running on Jenkins on multiple cores
    print "Checking for Email with subject: %s" % subject
    mail_connection.select("inbox")  # connect to inbox.
    # search the inbox for given email-subject
    result, [msg_ids] = mail_connection.search(None, '(SUBJECT "%s")' % subject)
    if msg_ids:
        print "Email(s) found with subject: %s" % subject
        msg_ids = ','.join(msg_ids.split(' '))
        # Change the Deleted flag to delete the email from Inbox
        mail_connection.store(msg_ids, '+FLAGS', r'(\Deleted)')
        status, response = mail_connection.expunge()
        assert status == 'OK'
        print "Email(s) deleted with subject: %s" % subject
        mail_connection.close()
        mail_connection.logout()
    return msg_ids


def assert_campaign_send(response, campaign, user, expected_count=1, email_client=False,
                         expected_status=200, abort_time_for_sends=40):
    """
    This assert that campaign has successfully been sent to candidates and campaign blasts and
    sends have been updated as expected. It then checks the source URL is correctly formed or
    in database table "url_conversion".
    """
    assert response.status_code == expected_status
    assert response.json()
    if not email_client:
        json_resp = response.json()
        assert str(campaign.id) in json_resp['message']
    # Need to add this as processing of POST request runs on Celery
    blasts = get_blasts_with_polling(campaign)

    assert blasts, 'Email campaign blasts not found'
    assert len(blasts) == 1
    # assert on sends
    assert_blast_sends(campaign, expected_count, abort_time_for_sends=abort_time_for_sends)
    campaign_sends = campaign.sends.all()
    assert len(campaign_sends) == expected_count
    sends_url_conversions = []
    # assert on activity of individual campaign sends
    for campaign_send in campaign_sends:
        # Get "email_campaign_send_url_conversion" records
        sends_url_conversions.extend(campaign_send.url_conversions)
        if not email_client:
            CampaignsTestsHelpers.assert_for_activity(user.id,
                                                      Activity.MessageIds.CAMPAIGN_EMAIL_SEND,
                                                      campaign_send.id)
    if campaign_sends:
        # assert on activity for whole campaign send
        CampaignsTestsHelpers.assert_for_activity(user.id,
                                                  Activity.MessageIds.CAMPAIGN_SEND,
                                                          campaign.id)
        # TODO: commenting till find exact reason of failing
        # if not email_client:
        #     assert poll(assert_and_delete_email, step=3, args=(campaign.subject,), timeout=60), \
        #         "Email with subject %s was not found." % campaign.subject

    # For each url_conversion record we assert that source_url is saved correctly
    for send_url_conversion in sends_url_conversions:
        # get URL conversion record from database table 'url_conversion' and delete it
        # delete url_conversion record
        assert str(
            send_url_conversion.url_conversion.id) in send_url_conversion.url_conversion.source_url
        UrlConversion.delete(send_url_conversion.url_conversion)


def get_blasts(campaign):
    """
    This returns all the blasts associated with given campaign
    """
    db.session.commit()
    return campaign.blasts.all()


def get_sends(campaign, blast_index, expected_count):
    """
    This returns all number of sends associated with given blast index of a campaign
    """
    db.session.commit()
    # TODO: Why did we add try catch here? Maybe we wanna catch here IndexError or something?
    try:
        if campaign.blasts[blast_index].sends == expected_count:
            return campaign.blasts[blast_index].sends
        else:
            return False
    except Exception:
        return False


def get_blasts_with_polling(campaign):
    """
    This polls the result of blasts of a campaign for 10s.
    """
    return poll(get_blasts, step=3, args=(campaign,), timeout=300)


def assert_blast_sends(campaign, expected_count, blast_index=0, abort_time_for_sends=100):
    """
    This function asserts the particular blast of given campaign has expected number of sends
    """
    time.sleep(10)
    sends = poll(get_sends, step=3, args=(campaign, blast_index, expected_count), timeout=abort_time_for_sends)
    assert sends >= expected_count


def post_to_email_template_resource(access_token, data):
    """
    Function sends a post request to email-templates,
    i.e. EmailTemplate/post()
    """
    response = requests.post(url=EmailCampaignUrl.TEMPLATES,
                             data=json.dumps(data),
                             headers={'Authorization': 'Bearer %s' % access_token,
                                      'Content-type': 'application/json'}
                             )
    return response


def request_to_email_template_resource(access_token, request, email_template_id, data=None):
    """
    Function sends a request to email template resource
    :param access_token: Token for user authorization
    :param request: get, post, patch, delete
    :param email_template_id: Id of email template
    :param data: data in form of dictionary
    """
    url = EmailCampaignUrl.TEMPLATES + '/' + str(email_template_id)
    return define_and_send_request(access_token, request, url, data)


def get_template_folder(token):
    """
    Function will create and retrieve template folder
    :param token:
    :return: template_folder_id, template_folder_name
    """
    template_folder_name = 'test_template_folder_%i' % datetime.datetime.now().microsecond

    data = {'name': template_folder_name}
    response = requests.post(url=EmailCampaignUrl.TEMPLATES_FOLDER, data=json.dumps(data),
                             headers={'Authorization': 'Bearer %s' % token,
                                      'Content-type': 'application/json'})
    assert response.status_code == requests.codes.CREATED
    response_obj = response.json()
    template_folder_id = response_obj["template_folder_id"][0]
    return template_folder_id['id'], template_folder_name


def create_email_template(token, user_id, template_name, body_html, body_text, is_immutable=1,
                          folder_id=None):
    """
    Creates a email campaign template with params provided

    :param token
    :param user_id:                 User id
    :param template_name:           Template name
    :param body_html:               Body html
    :param body_text:               Body text
    :param is_immutable:            1 if immutable, otherwise 0
    :param folder_id:               folder id
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

    create_resp = post_to_email_template_resource(token, data=data)
    return create_resp


def update_email_template(email_template_id, request, token, user_id, template_name, body_html,
                          body_text='',
                          folder_id=None, is_immutable=1):
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


def add_email_template(token, template_owner, template_body):
    """
    This function will create email template
    """
    domain_id = template_owner.domain_id

    # Add 'CAN_CREATE_EMAIL_TEMPLATE' to template_owner
    add_role_to_test_user(template_owner, [DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE,
                                           DomainRole.Roles.CAN_CREATE_EMAIL_TEMPLATE_FOLDER])

    # Get Template Folder Id
    template_folder_id, template_folder_name = get_template_folder(token)

    template_name = 'test_email_template%i' % datetime.datetime.now().microsecond
    is_immutable = 1
    resp = create_email_template(token, template_owner.id, template_name, template_body, '',
                                 is_immutable,
                                 folder_id=template_folder_id)
    db.session.commit()
    resp_obj = resp.json()
    resp_dict = resp_obj['template_id'][0]

    return {"template_id": resp_dict['id'],
            "template_folder_id": template_folder_id,
            "template_folder_name": template_folder_name,
            "template_name": template_name,
            "is_immutable": is_immutable,
            "domain_id": domain_id}


def template_body():
    return '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ' \
           '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\r\n<html>\r\n<head>' \
           '\r\n\t<title></title>\r\n</head>\r\n<body>\r\n<p>test campaign mail testing through script</p>' \
           '\r\n</body>\r\n</html>\r\n'


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
        url=EmailCampaignUrl.CAMPAIGNS,
        data=data,
        headers={'Authorization': 'Bearer %s' % access_token,
                 'content-type': 'application/json'}
    )
    return response


def create_data_for_campaign_creation(access_token, talent_pipeline, subject,
                                      campaign_name=fake.name(), assert_candidates=True):
    """
    This function returns the required data to create an email campaign
    :param access_token: access token of user
    :param talent_pipeline: talent_pipeline of user
    :param subject: Subject of campaign
    :param campaign_name: Name of campaign
    """
    email_from = 'no-reply@gettalent.com'
    reply_to = fake.safe_email()
    body_text = fake.sentence()
    body_html = "<html><body><h1>%s</h1></body></html>" % body_text
    smartlist_id, _ = create_smartlist_with_candidate(access_token,
                                                      talent_pipeline,
                                                      assert_candidates=assert_candidates)
    return {'name': campaign_name,
            'subject': subject,
            'from': email_from,
            'reply_to': reply_to,
            'body_html': body_html,
            'body_text': body_text,
            'frequency_id': Frequency.ONCE,
            'list_ids': [smartlist_id]
            }


def send_campaign_email_to_candidate(campaign, email, candidate_id, blast_id):
    """
    This function will create a campaign send object and then it will send the email to given email address.
    :param campaign: EmailCampaign object
    :param email: CandidateEmail object
    :param candidate_id: candidate unique id
    :param blast_id: campaign blast id
    """
    # Create an campaign send object
    email_campaign_send = EmailCampaignSend(campaign_id=campaign.id,
                                            candidate_id=candidate_id,
                                            sent_datetime=datetime.datetime.now(),
                                            blast_id=blast_id)
    EmailCampaignSend.save(email_campaign_send)

    # Send email to given email address with some random text as body.
    email_response = send_email(source='"%s" <no-reply@gettalent.com>' % campaign._from,
                                # Emails will be sent from <no-reply@gettalent.com> (verified by Amazon SES)
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
    if request.param == 'with_client':
        email_campaign.update(email_client_id=EmailClient.get_id_by_name('Browser'))
    # send campaign
    send_campaign(email_campaign, access_token)
    return email_campaign


def assert_campaign_failure(response, campaign, email_client=False,
                         expected_status=200):
    """
    This asserts that if some data was invalid while sending the campaign,
    campaign sending fails and no blasts are created.
    """
    assert response.status_code == expected_status
    assert response.json()
    if not email_client:
        json_resp = response.json()
        assert str(campaign.id) in json_resp['message']
    # Need to add this as processing of POST request runs on Celery
    blasts = get_blasts(campaign)
    assert not blasts, 'Email campaign blasts found for campaign (id:%d)' % campaign.id
    assert len(blasts) == 0
