# Standard Imports
import time
import json
import requests

# Application Specific
from email_campaign_service.common.models.db import db
from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import fake
from email_campaign_service.common.models.user import DomainRole
from email_campaign_service.common.routes import EmailCampaignUrl
from email_campaign_service.common.models.email_campaign import (EmailCampaign,
                                                                 EmailClient)
from email_campaign_service.common.utils.handy_functions import (add_role_to_test_user,
                                                                 raise_if_not_instance_of)
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import \
    create_smartlist_from_api
from email_campaign_service.common.utils.candidate_service_calls import \
    create_candidates_from_candidate_api

__author__ = 'basit'


def create_email_campaign(user):
    """
    This creates an email campaign for given user
    """
    email_campaign_name = fake.name()
    email_campaign_subject = fake.sentence()
    campaign_body_html = "<html><body>Email campaign test</body></html>"
    email_campaign = EmailCampaign(name=email_campaign_name,
                                   user_id=user.id,
                                   is_hidden=0,
                                   email_subject=email_campaign_subject,
                                   email_from=fake.safe_email(),
                                   email_reply_to=fake.email(),
                                   email_body_html=campaign_body_html,
                                   email_body_text="Email campaign test"
                                   )
    EmailCampaign.save(email_campaign)
    return email_campaign


def assign_roles(user):
    """
    This assign required permission to given user
    :param user:
    :return:
    """
    add_role_to_test_user(user, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                 DomainRole.Roles.CAN_GET_CANDIDATES])


def create_email_campaign_smartlist(access_token, talent_pool, campaign,
                                    emails_list=True, count=1):
    """
    This associates smartlist ids with given campaign
    """
    # create candidate
    smartlist_id, candidate_ids = create_smartlist_with_candidate(access_token,
                                                                  talent_pool,
                                                                  emails_list=emails_list,
                                                                  count=count)

    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=campaign.id)
    return campaign


def create_smartlist_with_candidate(access_token, talent_pool, emails_list=True, count=1):
    """
    This creates candidate(s) as specified by the count,  and assign it to a smartlist.
    Finally it returns smartlist_id and candidate_ids.
    """
    # create candidate
    data = FakeCandidatesData.create(talent_pool=talent_pool, emails_list=emails_list, count=count)
    candidate_ids = create_candidates_from_candidate_api(access_token, data,
                                                         return_candidate_ids_only=True)
    smartlist_data = {'name': fake.word(),
                      'candidate_ids': candidate_ids}
    smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
    smartlist_id = smartlists['smartlist']['id']
    return smartlist_id, candidate_ids


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


def send_campaign(campaign, access_token, sleep_time=20):
    """
    This function sends the campaign via /v1/email-campaigns/:id/send
    sleep_time is set to be 20s here. One can modify this by passing required value.
    :param campaign: Email campaign obj
    :param access_token: Auth token to make HTTP request
    :param sleep_time: time in seconds to wait for the task to be run on Celery.
    """
    raise_if_not_instance_of(campaign, EmailCampaign)
    raise_if_not_instance_of(access_token, basestring)
    # send campaign
    campaign.update(email_client_id=EmailClient.get_id_by_name('Browser'))
    response = requests.post(EmailCampaignUrl.SEND % campaign.id,
                             headers=dict(Authorization='Bearer %s' % access_token))
    assert response.ok
    time.sleep(sleep_time)
    db.session.commit()


def post_to_email_template_resource(access_token, data, domain_id=None):
    """
    Function sends a post request to email-templates,
    i.e. EmailTemplate/post()
    :param access_token
    :param data
    :param domain_id
    """
    response = requests.post(
            url=EmailCampaignUrl.EMAIL_TEMPLATE, data=json.dumps(data),
            headers={'Authorization': 'Bearer %s' % access_token,
                     'Content-type': 'application/json'}
    )
    return response


def response_info(resp_request, resp_json, resp_status):
    """
    Function returns the following information about the request:
        1. Request, 2. Response dict, and 3. Response status
    :param resp_request
    :type resp_json:        dict
    :type resp_status:      int
    """
    args = (resp_request, resp_json, resp_status)
    return "\nRequest: %s \nResponse JSON: %s \nResponse status: %s" % args


def define_and_send_request(request_method, url, access_token, template_id=None, data=None):
    """
    Function will define request based on params and make the appropriate call.
    :param  request_method:  can only be get, post, put, patch, or delete
    :param url
    :param access_token
    :param template_id
    :param data
    """
    request_method = request_method.lower()
    assert request_method in ['get', 'put', 'patch', 'delete']
    method = getattr(requests, request_method)
    if not data:
        data = dict(id=template_id)
    return method(url=url, data=json.dumps(data), headers={'Authorization': 'Bearer %s' % access_token})


def request_to_email_template_resource(access_token, request, email_template_id, data=None):
    """
    Function sends a request to email template resource
    :param access_token
    :param request: get, post, patch, delete
    :param email_template_id
    :param data
    """
    url = EmailCampaignUrl.EMAIL_TEMPLATE
    return define_and_send_request(request, url, access_token, email_template_id, data)


def get_template_folder(token):
    """
    Function will create and retrieve template folder
    :param token:
    :return: template_folder_id, template_folder_name
    """
    template_folder_name = 'test_template_folder_%i' % time.time()

    data = {'name': template_folder_name}
    response = requests.post(
            url=EmailCampaignUrl.EMAIL_TEMPLATE_FOLDER, data=json.dumps(data),
            headers={'Authorization': 'Bearer %s' % token,
                     'Content-type': 'application/json'}
    )
    assert response.status_code == 201
    response_obj = response.json()
    template_folder_id = response_obj["template_folder_id"][0]
    return template_folder_id['id'], template_folder_name


def create_email_template(token, user_id, template_name, body_html, body_text, is_immutable="1",
                          folder_id=None, domain_id=None, role_id=None):
    """
    Creates a email campaign template with params provided

    :param token
    :param user_id:                 User id
    :param template_name:           Template name
    :param body_html:               Body html
    :param body_text:               Body text
    :param is_immutable:            "1" if immutable, otherwise "0"
    :param folder_id:               folder id
    :param domain_id                domain_id
    :param role_id                  user scoped role id
    :return:                        Id of template created
    """
    # Check the user has role to create template
    role = DomainRole.query.get(role_id)
    domain_role_name = role.role_name
    assert domain_role_name == "CAN_CREATE_EMAIL_TEMPLATE"
    data = dict(
            name=template_name,
            email_template_folder_id=folder_id,
            user_id=user_id,
            type=0,
            email_body_html=body_html,
            email_body_text=body_text,
            is_immutable=is_immutable
    )

    create_resp = post_to_email_template_resource(token, data=data, domain_id=domain_id)
    return create_resp


def update_email_template(email_template_id, request, token, user_id, template_name, body_html, body_text='',
                          is_immutable="1", folder_id=None, domain_id=None):
    """

    :param email_template_id
    :param request
    :param token:
    :param user_id:
    :param template_name:
    :param body_html:
    :param body_text:
    :param is_immutable:
    :param folder_id:
    :param domain_id:
    :return:
    """
    data = dict(
            id=email_template_id,
            name=template_name,
            email_template_folder_id=folder_id,
            user_id=user_id,
            type=0,
            email_body_html=body_html,
            email_body_text=body_text,
            is_immutable=is_immutable
    )

    create_resp = request_to_email_template_resource(token, request, email_template_id, data)
    return create_resp


def add_domain_role(role_name, domain_id):
    """
    Function to create user roles for test purpose only
    :param role_name: Name of user role
    :param domain_id: user's domain ID
    :return:
    """
    domain_role = db.session.query(DomainRole).filter_by(role_name=role_name).first()
    if domain_role and domain_id == domain_role.domain_id:
        return domain_role.id
    elif domain_role:
        role_id = domain_role.id
        del_domain_roles(role_id)
        add_role = DomainRole(role_name=role_name, domain_id=domain_id)
        db.session.add(add_role)
        db.session.commit()
        role_id = add_role.id
        return role_id

    add_role = DomainRole(role_name=role_name, domain_id=domain_id)
    db.session.add(add_role)
    db.session.commit()
    role_id = add_role.id
    return role_id


def del_domain_roles(role_ids):
    """
    Function to delete all created user domain roles for tests
    :param role_ids: ids for roles to be deleted
    """
    if isinstance(role_ids, list):
        for role_id in role_ids:
            db.session.query(DomainRole).filter_by(id=role_id).delete()
            db.session.commit()
    else:
        db.session.query(DomainRole).filter_by(id=role_ids).delete()
