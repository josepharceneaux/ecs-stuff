"""
 Author: Jitesh Karesia, New Vision Software, <jitesh.karesia@newvisionsoftware.in>
         Um-I-Hani, QC-Technologies, <haniqadri.qc@gmail.com>
         Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

This file contains fixtures for tests of email-campaign-service
"""

__author__ = 'basit'

# Standard Library
from datetime import timedelta

# Application Specific
from email_campaign_service.common.tests.conftest import *
from email_campaign_service.modules.email_clients import SMTP
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.models.misc import Frequency
from email_campaign_service.common.routes import GraphqlServiceApiUrl
from email_campaign_service.common.models.candidate import CandidateEmail
from email_campaign_service.modules.utils import do_mergetag_replacements
from email_campaign_service.common.utils.datetime_utils import DatetimeUtils
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.campaign_services.tests_helpers import CampaignsTestsHelpers
from email_campaign_service.common.models.email_campaign import (EmailClient, UserEmailTemplate,
                                                                 EmailTemplateFolder, EmailCampaign,
                                                                 EmailClientCredentials)
from email_campaign_service.common.routes import (EmailCampaignApiUrl, CandidateApiUrl)
from email_campaign_service.tests.modules.handy_functions import (create_email_campaign,
                                                                  create_email_campaign_smartlist,
                                                                  send_campaign_helper,
                                                                  create_smartlist_with_given_email_candidate,
                                                                  add_email_template,
                                                                  get_template_folder, assert_valid_template_folder,
                                                                  EmailCampaignTypes, data_for_creating_email_clients,
                                                                  create_data_for_campaign_creation,
                                                                  create_email_campaign_via_api,
                                                                  send_campaign_with_client_id,
                                                                  create_email_campaign_with_merge_tags)

GRAPHQL_BASE_URL = GraphqlServiceApiUrl.GRAPHQL

EMAIL_CAMPAIGN_TYPES = [EmailCampaignTypes.WITHOUT_CLIENT, EmailCampaignTypes.WITH_CLIENT]


@pytest.fixture()
def email_campaign_of_user_first(user_first):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    """
    campaign = create_email_campaign(user_first)
    return campaign


@pytest.fixture()
def email_campaign_of_user_second(user_same_domain):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    """
    campaign = create_email_campaign(user_same_domain)
    return campaign


@pytest.fixture()
def email_campaign_in_other_domain(access_token_other, user_from_diff_domain, talent_pipeline_other):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    for user in different domain
    """
    campaign = create_email_campaign(user_from_diff_domain)
    create_email_campaign_smartlist(access_token_other, talent_pipeline_other, campaign)
    return campaign


@pytest.fixture()
def campaign_with_candidate_having_no_email(email_campaign_of_user_first, access_token_first, talent_pipeline):
    """
    This creates a campaign which has candidates associated having no email
    """
    campaign = create_email_campaign_smartlist(access_token_first, talent_pipeline,
                                               email_campaign_of_user_first, emails_list=False)
    return campaign


@pytest.fixture()
def campaign_with_two_candidates(email_campaign_of_user_first, access_token_first, talent_pipeline):
    """
    This returns a campaign which has two candidates associated having email address.
    """
    campaign = create_email_campaign_smartlist(access_token_first, talent_pipeline, email_campaign_of_user_first,
                                               count=2)
    return campaign


@pytest.fixture()
def email_campaign_with_merge_tags(user_first, access_token_first, headers, talent_pipeline, outgoing_email_client):
    """
    This fixture creates an email campaign in which body_text and body_html contains merge tags.
    """
    email_campaign = create_email_campaign_with_merge_tags(user_first)
    # We want that campaign is sent via SMTP server
    email_campaign.update(email_client_credentials_id=outgoing_email_client)
    smartlist_id, candidate_id = CampaignsTestsHelpers.create_smartlist_with_candidate(access_token_first,
                                                                                       talent_pipeline,
                                                                                       emails_list=True,
                                                                                       assert_candidates=True)
    create_email_campaign_smartlists(smartlist_ids=[smartlist_id], email_campaign_id=email_campaign.id)
    candidate_get_response = requests.get(CandidateApiUrl.CANDIDATE % candidate_id[0], headers=headers)
    return email_campaign, candidate_get_response.json()['candidate']


@pytest.fixture(params=EMAIL_CAMPAIGN_TYPES)
def campaign_with_and_without_client(request, access_token_first, talent_pipeline, email_campaign_of_user_first):
    """
    This fixture creates campaign 1) with client_id and 2) without client id.
    """
    email_campaign = create_email_campaign_smartlist(access_token_first, talent_pipeline,
                                                     email_campaign_of_user_first, count=1)

    if request.param == EmailCampaignTypes.WITH_CLIENT:
        email_campaign.update(email_client_id=EmailClient.get_id_by_name('Browser'))
    return email_campaign


@pytest.fixture()
def campaign_with_multiple_candidates_email(email_campaign_of_user_first, access_token_first, talent_pipeline):
    """
    This returns a campaign which has 2 candidates associated and have 2 email address.
    Email should be send to only one address of both candidates
    """
    _emails = [
        # Primary and work label
        [{'label': 'work', 'address': 'work' + fake.safe_email()},
         {'label': 'primary', 'address': 'primary' + fake.safe_email()}],
        # Work and home label
        [{'label': 'work', 'address': 'work' + fake.safe_email()},
         {'label': 'home', 'address': 'home' + fake.safe_email()}],
    ]

    campaign = create_smartlist_with_given_email_candidate(access_token_first, campaign=email_campaign_of_user_first,
                                                           talent_pipeline=talent_pipeline, emails=_emails, count=2)
    return campaign


@pytest.fixture()
def campaign_to_ten_candidates_not_sent(email_campaign_of_user_first, access_token_first, talent_pipeline):
    """
    This returns a campaign which has ten candidates associated having email addresses.
    """
    campaign = create_email_campaign_smartlist(access_token_first, talent_pipeline,
                                               email_campaign_of_user_first, count=10)
    return campaign


@pytest.fixture()
def campaign_with_candidates_having_same_email_in_diff_domain(campaign_with_two_candidates,
                                                              candidate_in_other_domain):
    """
    This returns a campaign which has one candidate associated having email address.
    One more candidate exist in some other domain having same email address.
    """
    same_email = fake.email()
    campaign_with_two_candidates.user.candidates[0].emails[0].update(address=same_email)
    candidate_in_other_domain.emails[0].update(address=same_email)
    return campaign_with_two_candidates


@pytest.fixture()
def campaign_with_same_candidate_in_multiple_smartlists(email_campaign_of_user_first, talent_pipeline,
                                                        access_token_first):
    """
    This fixture creates an email campaign with two smartlists.
    Smartlist 1 will have two candidates and smartlist 2 will have one candidate (which will be
    same as one of the two candidates of smartlist 1).
    """
    smartlist_ids = CampaignsTestsHelpers.get_two_smartlists_with_same_candidate(talent_pipeline, access_token_first,
                                                                                 email_list=True)
    create_email_campaign_smartlists(smartlist_ids=smartlist_ids, email_campaign_id=email_campaign_of_user_first.id)

    return email_campaign_of_user_first


@pytest.fixture()
def candidate_in_other_domain(user_from_diff_domain):
    """
    Here we create a candidate for `user_from_diff_domain`
    """
    candidate = Candidate(last_name=gen_salt(20), first_name=gen_salt(20),
                          user_id=user_from_diff_domain.id)
    Candidate.save(candidate)
    candidate_email = CandidateEmail(candidate_id=candidate.id,
                                     address=gen_salt(20), email_label_id=CandidateEmail.labels_mapping['Primary'])
    CandidateEmail.save(candidate_email)
    return candidate


@pytest.fixture(params=EMAIL_CAMPAIGN_TYPES)
def sent_campaign(request, campaign_with_two_candidates, access_token_first):
    """
    This fixture sends the campaign 1) with client_id and 2) without client id
    via /v1/email-campaigns/:id/send and returns the email-campaign obj.
    """
    return send_campaign_helper(request, campaign_with_two_candidates, access_token_first)


@pytest.fixture(params=EMAIL_CAMPAIGN_TYPES)
def sent_campaign_in_other_domain(request, email_campaign_in_other_domain, access_token_other):
    """
    This fixture sends the campaign_in_other_domain 1) with client_id and 2) without client id
    via /v1/email-campaigns/:id/send and returns the email-campaign obj.
    """
    return send_campaign_helper(request, email_campaign_in_other_domain, access_token_other)


@pytest.fixture(params=EMAIL_CAMPAIGN_TYPES)
def sent_campaign_multiple_email(request, campaign_with_multiple_candidates_email, access_token_first):
    """
    This fixture sends the campaign via /v1/email-campaigns/:id/send and returns the
    email-campaign obj.
    """
    return send_campaign_helper(request, campaign_with_multiple_candidates_email,
                                access_token_first)


@pytest.fixture(params=EMAIL_CAMPAIGN_TYPES)
def sent_campaign_to_ten_candidates(request, campaign_to_ten_candidates_not_sent, access_token_first):
    """
    This fixture sends the given campaign 1) with client_id and 2) without client id
    via /v1/email-campaigns/:id/send and returns the email-campaign obj.
    """
    return send_campaign_helper(request, campaign_to_ten_candidates_not_sent, access_token_first)


@pytest.fixture()
def send_email_campaign_by_client_id_response(access_token_first, campaign_with_two_candidates):
    """
    This fixture is used to get the response of sending campaign emails with client id
    for a particular campaign. It also ensures that response is in proper format. Used in
    multiple tests.
    :param access_token_first: Bearer token for authorization.
    :param campaign_with_two_candidates: EmailCampaign object with a valid candidate associated.
    """
    return send_campaign_with_client_id(campaign_with_two_candidates, access_token_first)


@pytest.fixture()
def template_id(domain_id):
    """
    Retrieves email template for the test email campaign
    :return:    Id of template retrieved
    """
    # Retrieve campaign template from 'Sample Templates' folder
    template_folder = EmailTemplateFolder.get_by_name_and_domain_id('Sample Templates', domain_id)
    template_folder_id = template_folder.id
    template = db.session.query(UserEmailTemplate).filter_by(template_folder_id=template_folder_id)

    return template['id']


@pytest.fixture(params=['name', 'subject', 'body_html', 'frequency_id', 'list_ids'])
def invalid_data_for_campaign_creation(request):
    """
    This function returns the data to create an email campaign. It also removes a required
    field from data to make it invalid.
    Required fields are 'name', 'subject', 'body_html', 'frequency_id', 'list_ids'
    """
    email_from = 'no-reply@gettalent.com'
    reply_to = fake.safe_email()
    body_text = fake.sentence()
    body_html = "<html><body><h1>%s</h1></body></html>" % body_text
    campaign_data = {'name': fake.name(),
                     'subject': fake.sentence(),
                     'description': fake.paragraph(),
                     'from': email_from,
                     'reply_to': reply_to,
                     'body_html': body_html,
                     'body_text': body_text,
                     'frequency_id': Frequency.ONCE,
                     'list_ids': [fake.random_number()]
                     }
    del campaign_data[request.param]
    return campaign_data, request.param


@pytest.fixture()
def create_email_template_folder(headers, user_first):
    """
    Here we create email-template-folder
    """
    template_folder_id, template_folder_name = get_template_folder(headers)
    # Assert that folder is created with correct name
    response = requests.get(EmailCampaignApiUrl.TEMPLATE_FOLDER % template_folder_id,
                            headers=headers)
    assert response.ok
    assert response.json()
    json_response = response.json()
    assert_valid_template_folder(json_response['email_template_folder'], user_first.domain.id,
                                 template_folder_name)
    return template_folder_id, template_folder_name


@pytest.fixture()
def email_template(headers, user_first):
    """
    Here we create email-template-folder
    """
    return add_email_template(headers, user_first)


@pytest.fixture()
def email_templates_bulk(headers, user_first):
    """
    Here we create 10 email-templates to test pagination.
    """
    email_template_ids = []
    for _ in xrange(1, 11):
        template = add_email_template(headers, user_first)
        email_template_ids.append(template['id'])
    return email_template_ids


@pytest.fixture()
def email_clients(request, headers):
    """
    This add 3 email clients for user_first.
    :rtype: list
    """
    email_client_ids = []
    for email_client_data in data_for_creating_email_clients():
        print 'connecting with host:%s' % email_client_data['host']
        response = requests.post(EmailCampaignApiUrl.EMAIL_CLIENTS, headers=headers, data=json.dumps(email_client_data))
        assert response.ok
        assert 'id' in response.json()
        email_client_ids.append(response.json()['id'])

    def fin():  # Better to have finalizer here so that importer does not need to import all the accounts
        try:
            [EmailClientCredentials.delete(email_client_id) for email_client_id in email_client_ids]
        except Exception:
            pass
    request.addfinalizer(fin)
    return email_client_ids


@pytest.fixture()
def outgoing_email_client(headers):
    """
    This add 3 outgoing(SMTP) email-clients for user_first.
    :rtype: list
    """
    email_clients_data = data_for_creating_email_clients(key='outgoing')
    for email_client_data in email_clients_data:
        response = requests.post(EmailCampaignApiUrl.EMAIL_CLIENTS, headers=headers, data=json.dumps(email_client_data))
        assert response.ok
        assert 'id' in response.json()
        return response.json()['id']


@pytest.fixture()
def email_campaign_with_outgoing_email_client(access_token_first, talent_pipeline, headers,
                                              outgoing_email_client):
    """
    This creates an email-campaign which will be sent via an SMTP server added by user.
    """
    subject = '%s-test_email_campaign_with_outgoing_email_client' % fake.uuid4()
    campaign_data = create_data_for_campaign_creation(access_token_first, talent_pipeline, subject)
    campaign_data['frequency_id'] = Frequency.DAILY
    campaign_data['start_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow() + timedelta(weeks=1))
    campaign_data['end_datetime'] = DatetimeUtils.to_utc_str(datetime.utcnow()
                                                             + timedelta(weeks=1) + timedelta(days=4))

    # GET email-client-id
    response = requests.get(EmailCampaignApiUrl.EMAIL_CLIENTS + '?type=outgoing', headers=headers)
    assert response.ok
    assert response.json()
    email_client_response = response.json()['email_client_credentials']
    assert len(email_client_response) == 1
    campaign_data['email_client_credentials_id'] = email_client_response[0]['id']

    response = create_email_campaign_via_api(access_token_first, campaign_data)
    assert response.status_code == requests.codes.CREATED
    resp_object = response.json()
    assert 'campaign' in resp_object and resp_object['campaign']
    db.session.commit()
    email_campaign = EmailCampaign.get_by_id(resp_object['campaign']['id'])
    assert email_campaign
    return email_campaign


@pytest.fixture()
def data_for_email_conversation_importer(email_clients, headers, user_first, candidate_first):
    """
    We need to
    - Send an email to 'gettalentmailtest@gmail.com'. For this we will add an SMTP client for the user.
    - Add an IMAP client for user to retrieve email-conversations (email_clients will server this purpose).
    We send email such that subject and body contains merge tags in it.
    """
    # Add candidate's email with value of test account "gettalentmailtest@gmail.com"
    candidate_email = CandidateEmail(candidate_id=candidate_first.id,
                                     address=app.config[TalentConfigKeys.GT_GMAIL_ID],
                                     email_label_id=CandidateEmail.labels_mapping['Primary'])
    CandidateEmail.save(candidate_email)
    # GET SMTP email-client-id
    response = requests.get(EmailCampaignApiUrl.EMAIL_CLIENT_WITH_ID % email_clients[0], headers=headers)
    assert response.ok
    assert response.json()
    email_client_response = response.json()['email_client_credentials']
    email_campaign = create_email_campaign_with_merge_tags(user_first, add_preference_url=False)
    [subject, body_text] = do_mergetag_replacements([email_campaign.subject, email_campaign.body_text],
                                                    candidate_first, candidate_email.address)
    # Send email
    print 'Sending email with SMTP server'
    client = SMTP(email_client_response['host'], email_client_response['port'],
                  email_client_response['email'], app.config[TalentConfigKeys.GT_GMAIL_PASSWORD])
    client.send_email(app.config[TalentConfigKeys.GT_GMAIL_ID], subject, body_text)
    # GET IMAP email-client-id
    response = requests.get(EmailCampaignApiUrl.EMAIL_CLIENT_WITH_ID % email_clients[1], headers=headers)
    assert response.ok
    assert response.json()
    imap_email_client_response = response.json()['email_client_credentials']
    return subject, body_text, imap_email_client_response
