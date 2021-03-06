__author__ = 'ufarooqi'
import re
import random
import string
from sqlalchemy import func
from urlparse import urlparse
from mixpanel_jql import JQL, Reducer
from werkzeug.security import gen_salt
from datetime import datetime, timedelta
from flask import render_template, request
from user_service.user_app import app, logger

from user_service.common.routes import get_web_app_url
from user_service.common.utils.validators import is_number
from user_service.common.models.candidate import Candidate
from user_service.common.utils.amazon_ses import send_email
from user_service.common.models.email_campaign import EmailCampaign, EmailCampaignSend
from user_service.common.models.talent_pools_pipelines import TalentPipeline
from user_service.common.error_handling import InvalidUsage, NotFoundError, UnauthorizedError
from user_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs
from user_service.common.models.email_campaign import EmailTemplateFolder, UserEmailTemplate
from user_service.common.models.user import db, Domain, User, UserGroup, Role
from user_service.common.utils.auth_utils import gettalent_generate_password_hash

PASSWORD_RECOVERY_JWT_SALT = \
    'yYut5isN6vLelCW4He0cHIXPSth7gY2OzOZKHS5uXbFvn84raYecMcdF002Br2ciexYfWOFKzZVU8M2rLJXql9vCLEmWlPIys118'
PASSWORD_RECOVERY_JWT_MAX_AGE_SECONDS = 12 * 3600  # Password recovery token expires after 12 hours


def get_or_create_domain(logged_in_user_id, name, usage_limitation=-1, organization_id=1, default_tracking_code=None,
                         expiration=None, default_culture_id=1, dice_company_id=None):
    """
    Gets or creates domain with given name.
    Returns domain id of domain found in database or newly created.
    :param str name: Domain name
    :param int usage_limitation
    :param int organization_id: Organization id to which this domain should get associated
    :param int default_culture_id: Culture id to which this domain should be associated
    :param int dice_company_id: Will connect the new or existing domain to this ID
    :return: domain id
    :rtype: int
    """

    # Check if domain exists
    domain = Domain.query.filter_by(name=name).first()
    if domain:
        if dice_company_id and not domain.dice_company_id:
            domain.dice_company_id = dice_company_id
            db.session.commit()
        return domain.id

    else:
        # Create domain if it doesn't exist
        domain = Domain(name=name, usage_limitation=usage_limitation, organization_id=organization_id,
                        default_tracking_code=default_tracking_code, default_culture_id=default_culture_id,
                        dice_company_id=dice_company_id, expiration=expiration)
        db.session.add(domain)
        db.session.commit()

        get_or_create_default_email_templates(domain.id, logged_in_user_id)

        # get_or_create_rating_custom_fields(domain_id)
        return domain.id


def check_if_user_exists(email):
    # Get user if user exists
    domain_user = User.query.filter(User.email == email).first()
    return domain_user if domain_user else False


def create_user_for_company(first_name, last_name, email, domain_id, expiration_date=None, phone="",
                            dice_user_id=None, thumbnail_url='', user_group_id=None, locale=None, role_id=None):

    from dateutil import parser
    expiration = None
    if expiration_date:
        try:
            expiration = parser.parse(expiration_date)
        except Exception as e:
            raise InvalidUsage(error_message="Expiration date %s is invalid because: %s" % (expiration_date, e.message))

    # create user for existing domain
    user = create_user(email=email, domain_id=domain_id, first_name=first_name, last_name=last_name, phone=phone,
                       expiration=expiration, dice_user_id=dice_user_id, thumbnail_url=thumbnail_url,
                       user_group_id=user_group_id, locale=locale, role_id=role_id)

    return user.id


def validate_role(role, request_domain_id, request_user):
    """
    This method will validate given role and permissions of the requesting user.
    :param int|basestring role: Role Name or ID
    :param request_domain_id: Id of the domain in which new user is going to be created
    :param request_user: User object of Logged-in user
    :return: Role Id
    :rtype: int
    """

    if is_number(role):
        role_object = Role.query.get(int(role))
        if role_object:
            role_id = role
            role_name = role_object.name
        else:
            raise NotFoundError("Role with id:%s doesn't exist in database" % role)
    else:
        role_object = Role.get_by_name(role)
        if role_object:
            role_id = role_object.id
            role_name = role_object.name
        else:
            raise NotFoundError("Role with name:%s doesn't exist in database" % role)

    if request_user.role.name != 'TALENT_ADMIN' and (
                    request_domain_id != request_user.domain_id or role_name == 'TALENT_ADMIN'):
        raise UnauthorizedError("User %s doesn't have appropriate permissions to assign "
                                "given role: (%s)" % role_name )

    return role_id


def get_or_create_default_email_templates(domain_id, admin_user_id):

    sample_templates_folder = EmailTemplateFolder.query.filter(EmailTemplateFolder.domain_id == domain_id,
                                                               EmailTemplateFolder.name == 'Sample Templates').first()

    if not sample_templates_folder:
        # Create the Sample Templates folder if it doesn't exist
        sample_templates_folder = EmailTemplateFolder(name='Sample Templates', domain_id=domain_id, parent_id=None,
                                                      is_immutable=0)
        db.session.add(sample_templates_folder)
        db.session.commit()

    sample_templates = UserEmailTemplate.query.filter(UserEmailTemplate.template_folder_id == sample_templates_folder.id)
    sample_template_names = [t.name for t in sample_templates]

    if ('Announcement' not in sample_template_names) and ('Intro' not in sample_template_names):
        # Create the sample templates if they don't exist
        get_talent_special_announcement = render_template('getTalentSpecialAnnouncement.html')
        get_talent_intro = render_template('getTalentIntro.html')

        announcement_template = UserEmailTemplate(user_id=admin_user_id, type='0', name='Announcement',
                                                  body_html=get_talent_special_announcement, body_text='',
                                                  template_folder_id=sample_templates_folder.id, is_immutable='0')

        intro_template = UserEmailTemplate(user_id=admin_user_id, type='0', name='Intro',
                                           body_html=get_talent_intro, body_text='',
                                           template_folder_id=sample_templates_folder.id, is_immutable='0')

        db.session.add(announcement_template)
        db.session.add(intro_template)
        db.session.commit()

    return sample_templates_folder.id


def generate_temporary_password():
    """
    This method will generate random password which will have at least 2 letters, digits and special characters
    :return: Password
    """
    password = [random.choice(string.ascii_letters) for _ in range(3)] + [
        random.choice(string.digits) for _ in range(3)] + ['&', '#']
    random.shuffle(password)
    return ''.join(password)


def create_user(email, domain_id, first_name, last_name, expiration, phone="", dice_user_id=None,
                thumbnail_url='', user_group_id=None, locale=None, role_id=None):

    temp_password = gen_salt(8)
    hashed_password = gettalent_generate_password_hash(temp_password)

    user_group = None

    # Get user's group ID
    if not user_group_id:
        user_groups = UserGroup.all_groups_of_domain(domain_id=domain_id)
        if user_groups:  # TODO: this shouldn't be necessary since each domain must belong to a user_group
            user_group = user_groups[0]
    else:
        user_group = UserGroup.query.get(user_group_id)

    if not user_group:
        raise InvalidUsage("Either user_group_id is not provided or no group exists in user's domain")

    if user_group.domain_id != domain_id:
        raise InvalidUsage("User Group %s belongs to different domain" % user_group.id)

    user_data_dict = dict(
            email=email, domain_id=domain_id, first_name=first_name, last_name=last_name, expiration=expiration,
            dice_user_id=dice_user_id, password=hashed_password, phone=phone, thumbnail_url=thumbnail_url,
            user_group_id=user_group.id, locale=locale, is_disabled=False, role_id=role_id)

    user_data_dict = {k: v for k, v in user_data_dict.items() if v}

    # Make new entry in user table
    user = User(**user_data_dict)
    db.session.add(user)
    db.session.commit()

    # TODO: Make new widget_page if first user in domain
    # TODO: Add activity

    send_new_account_email(email, temp_password, 'support@gettalent.com')

    return user


def validate_password(password):
    """
    This method will ensure that password has following characters:
    --> At least 2 alphabetical characters
    --> At least 2 Numeric characters
    --> At least 2 Special characters
    --> Length of password should be between 8 and 20
    :param password:
    :return: Boolean Value
    """
    pattern = re.compile('((?=.*\d.*\d)(?=.*[A-Za-z].*[A-Za-z])(?=.*[^a-zA-Z0-9].*[^a-zA-Z0-9]).{8,})')
    return pattern.match(password)


def send_new_account_email(account_email, temp_password, to_email):
    if app.config[TalentConfigKeys.ENV_KEY] in ('prod', 'qa'):
        login_url = '{}/login'.format(get_web_app_url())
        new_user_email = render_template('new_user.html', email=account_email, password=temp_password, login=login_url)
        send_email(source='"getTalent Registration" <support@gettalent.com>',
                   subject='Setup Your New Account',
                   body=new_user_email, to_addresses=[to_email], email_format='html')


def send_reset_password_email(email, name, reset_password_url, six_digit_token):
    new_user_email = render_template('reset_password.html', email=email, name=name, six_digit_token=six_digit_token,
                                     reset_password_url=reset_password_url)
    send_email(source='"getTalent Registration" <support@gettalent.com>',
               subject='getTalent password reset',
               body=new_user_email, to_addresses=[email], email_format='html')


def get_users_stats_from_mixpanel(user_data_dict, is_single_user=False, include_stats=False):
    """
    This method will fetch user stats from MixPanel using JQL and Candidate Table using SQL
    :param user_data_dict: Dict containing data for all users in system
    :param is_single_user: Are we getting stats for a single user
    :param include_stats: Include statistics of user in response
    :return: Dict containing data for all users in system
    :rtype: dict
    """

    if not include_stats:
        return user_data_dict

    if is_single_user:
        user_data_dict['candidates_count'] = 0
        user_data_dict['logins_per_month'] = 0
        user_data_dict['searches_per_month'] = 0
        user_data_dict['campaigns_count'] = 0
        user_data_dict['pipelines_count'] = 0
        user_data_dict['emails_count'] = 0
    else:
        for user_id, user_data in user_data_dict.iteritems():
            user_data['candidates_count'] = 0
            user_data['logins_per_month'] = 0
            user_data['searches_per_month'] = 0
            user_data['campaigns_count'] = 0
            user_data['pipelines_count'] = 0
            user_data['emails_count'] = 0

    request_origin = request.environ.get('HTTP_ORIGIN', '')
    logger.info('Request Origin for users GET request is: %s', request_origin)

    if not request_origin:
        url_prefix = 'staging.gettalent' if app.config[TalentConfigKeys.ENV_KEY] in (
            TalentEnvs.QA, TalentEnvs.DEV, TalentEnvs.JENKINS) else 'app.gettalent'
    else:
        parsed_url = urlparse(request_origin)
        url_prefix = parsed_url.netloc

    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=30)

    if is_single_user:
        selector = '"{}" in properties["$current_url"] and properties["id"] == {}'.format(url_prefix, user_data_dict['id'])
    else:
        selector = '"{}" in properties["$current_url"]'.format(url_prefix)

    params = {
        'event_selectors': [
            {
                'event': 'Login',
                'selector': selector
            },
            {
                'event': 'Search',
                'selector': selector
            }
        ],
        'from_date': str(from_date.date()),
        'to_date': str(to_date.date())
    }
    try:
        query = JQL(app.config[TalentConfigKeys.MIXPANEL_API_KEY], params).group_by(
                keys=["e.properties.id", "e.name"], accumulator=Reducer.count())
        iterator = query.send()
    except Exception as e:
        logger.error("Error while fetching user stats from MixPanel because: %s" % e.message)
        raise InvalidUsage("Error while fetching user stats")

    for row in iterator:
        user_dict_key = 'logins_per_month' if row['key'][1] == 'Login' else 'searches_per_month'
        if is_single_user and row['key'][0] == user_data_dict['id']:
            user_data_dict[user_dict_key] = row['value']
        elif (not is_single_user) and (row['key'][0] in user_data_dict):
            user_data_dict[row['key'][0]][user_dict_key] = row['value']

    # Get Candidate, Pipeline and Campaigns Stats of a User
    if is_single_user:
        user_data_dict['pipelines_count'] = TalentPipeline.query.filter_by(user_id=user_data_dict['id']).count()
        user_data_dict['campaigns_count'] = EmailCampaign.query.filter_by(user_id=user_data_dict['id']).count()
        user_data_dict['candidates_count'] = Candidate.query.filter_by(user_id=user_data_dict['id']).count()
        user_data_dict['emails_count'] = EmailCampaignSend.query.join(
                EmailCampaign).filter(EmailCampaign.user_id == user_data_dict['id']).count()

    else:
        users_candidate_count = db.session.query(Candidate.user_id,
                                                 func.count(Candidate.user_id)).group_by(Candidate.user_id).all()
        users_pipelines_count = db.session.query(TalentPipeline.user_id,
                                                 func.count(TalentPipeline.user_id)).group_by(TalentPipeline.user_id).all()
        users_campaigns_count = db.session.query(EmailCampaign.user_id,
                                                 func.count(EmailCampaign.user_id)).group_by(EmailCampaign.user_id).all()
        users_emails_count = EmailCampaignSend.query.join(EmailCampaign).with_entities(
                EmailCampaign.user_id, func.count(EmailCampaignSend.id)).group_by(
                EmailCampaign.user_id).all()

        for user_id, count in users_candidate_count:
            if user_id in user_data_dict:
                user_data_dict[user_id]['candidates_count'] = count

        for user_id, count in users_pipelines_count:
            if user_id in user_data_dict:
                user_data_dict[user_id]['pipelines_count'] = count

        for user_id, count in users_campaigns_count:
            if user_id in user_data_dict:
                user_data_dict[user_id]['campaigns_count'] = count

        for user_id, count in users_emails_count:
            if user_id in user_data_dict:
                user_data_dict[user_id]['emails_count'] = count

    return user_data_dict

