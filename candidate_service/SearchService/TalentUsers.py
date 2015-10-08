import re
# from TalentDiceClient import query_dice_company_id
# from handy_functions import is_number
import base64
import datetime

# from CustomErrors import CustomErrorResponse
#
# from gluon import current
# from TalentReporting import email_notification_to_admins
import requests
from flask.ext.sqlalchemy import SQLAlchemy
from flaskext.mysql import MySQL

RATING_CATEGORY_NAME = "Rating"
RATING_FIELDS = ('Overall', 'Presentation', 'Communication Skills', 'Interests', 'Academic Experience', 'Work Experience')
_USER_ID_TO_DOMAIN_ID_CACHE_KEY = '_user_id_to_domain_id_dict'

DEFAULT_USER_PASSWORD = "temp976892"
HMAC_KEY = "s!web976892"

#TALENT_CRYPT = CRYPT(min_length=8, key=HMAC_KEY, digest_alg='pbkdf2(1000,64,sha512)', error_message="We now require a minimum password length of 8. Please reset your password and try again.")  # for hashing passwords

from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column, Integer, String
engine = create_engine('mysql://root:root@localhost:3306/talent_local')
metadata = MetaData(bind=engine)
users = Table('user', metadata, autoload=True)

def users_in_domain(domain_id):
    """
    Returns all the users for provided domain id
    Uses cache
    params:
        domain_id: Domain id
    returns;
        database users in given domain

    :rtype: gluon.dal.objects.Rows
    """
    user_domain = users.select(users.c.domainId == domain_id).execute().first()
    return user_domain


def user_ids_in_domain(domain_id):
    """
    Returns list of user ids from given domain

    :rtype: list[int]
    """
    return [user.id for user in users_in_domain(domain_id)]


def user_from_id(user_id):
    """

    :rtype: gluon.dal.objects.Row
    """
    db = current.db
    user = db(db.user.id == user_id).select().first()
    if not user:
        current.logger.error("Couldn't find a user with user_id: %s", user_id)
        return None
    else:
        return user


def _create_user(email, hashed_password, registration_key, domain_id, first_name, last_name, expiration, dice_user_id=None, user_attributes=None,
                 is_active=True, is_admin=False):
    """

    :rtype: int
    """
    db = current.db

    user_id = db.user.insert(email=email, password=hashed_password, registration_key=registration_key, domainId=domain_id,
                             firstName=first_name, lastName=last_name, expiration=expiration, diceUserId=dice_user_id)

    if user_attributes:
        db.user_attributes.insert(userId=user_id, brand=user_attributes['brand'],
                                  department=user_attributes['department'], userGroup=user_attributes['userGroup'],
                                  KPI=user_attributes['KPI'])
    if not is_active:
        current.auth.add_membership(group_id=get_passive_user_group_id(), user_id=user_id)
    if is_admin:
        current.auth.add_membership(group_id=get_user_manager_group_id(), user_id=user_id)

    db.commit()

    # TODO: Remove this functionality when we'll add UI for user scoped roles
    add_roles_to_user(user_id)

    # Make new widget_page if first user in domain
    user = user_from_id(user_id)
    current.get_or_create_widget_page(user, domain_id=domain_id)

    # Add activity
    from TalentActivityAPI import TalentActivityAPI
    activity_api = TalentActivityAPI()
    activity_api.create(user_id, activity_api.USER_CREATE, source_table='user', source_id=user_id,
                        params=dict(firstName=first_name, lastName=last_name))

    return user_id


def add_roles_to_user(user_id):
    """
    :param user_id:
    :return: void
    """
    import json
    user = user_from_id(user_id)

    access_token = get_auth_service_access_token_from_session()
    refresh_token = get_auth_service_refresh_token_from_session()

    if access_token and refresh_token:
        # Refresh bearer token
        refresh_auth_service_access_token(refresh_token)
        access_token = get_auth_service_access_token_from_session()
        if user:
            data = {'roles': ['CAN_EDIT_CANDIDATE', 'CAN_SEND_CAMPAIGN']}  # Pass either role's name or role's Id
            try:
                response = requests.post(url=current.ADD_ROLES_TO_USER % user_id, data=json.dumps(data),
                                         headers={'content-type': 'application/json', 'Authorization': 'Bearer %s' % access_token})
                if response.status_code != 200:
                    error_message = response.json()['error_message']
                    current.logger.exception("Couldn't add roles to a user %s because of : %s" % (user_id, error_message))
            except Exception as e:
                current.logger.exception("Couldn't add roles to a user %s because of : %s" % (user_id, e.message))
    else:
        current.logger.error("add_roles_to_user: Access_Token or Refresh_Token is None")


def domain_from_id(domain_id):
    """

    :rtype: gluon.dal.objects.Row
    """
    db = current.db
    domain = db(db.domain.id == domain_id).select().first()
    if not domain:
        current.logger.error("Couldn't find a domain with domain_id: %s", domain_id)
        return None
    else:
        return domain


def domain_from_dice_company_id(dice_company_id):
    """

    :rtype: gluon.dal.objects.Row
    """
    db = current.db
    return db(db.domain.diceCompanyId == dice_company_id).select().first()


def get_or_create_domain(name, usage_limitation=-1, organization_id=1, default_culture_id=1, dice_company_id=None):
    """
    Gets or creates domain with given name.
    Returns domain id of domain found in database or newly created.
    :param name: Domain name
    :param usage_limitation:
    :param organization_id: Organization id to which this domain should get associated
    :param default_culture_id: Culture id to which this domain should be associated
    :param dice_company_id: Will connect the new or existing domain to this ID
    :return: domain id
    :rtype: int
    """
    db = current.db

    # Check if domain exists
    domain = db(
        (db.domain.name == name) &
        (db.domain.organizationId == organization_id)
    ).select().first()

    if domain:
        if dice_company_id and not domain.diceCompanyId:
            # Adds in the diceCompanyId if not already there
            current.logger.info("Domain %s was previously not Dice-connected. Will connect domain with Dice ID %s", name, dice_company_id)
            domain.update_record(diceCompanyId=dice_company_id)
        return domain.id

    # Create if it doesn't
    domain_id = db.domain.insert(name=name, usageLimitation=usage_limitation,
                                 organizationId=organization_id,
                                 defaultCultureId=default_culture_id,
                                 diceCompanyId=dice_company_id)
    get_or_create_rating_custom_fields(domain_id)
    return domain_id


def domain_id_from_user_id(user_id):
    db = current.db
    user = db(db.user.id == user_id).select().first()
    if not user:
        current.logger.error("domain_id_from_user_id(%s): Tried to find domain ID of user: ", user_id)
        return None
    if not user.domainId:
        current.logger.error("domain_id_from_user_id(%s): user.domainId was None!", user_id)
        return None
    return user.domainId


from dateutil import parser


def create_user_for_company(first_name, last_name, email, domain_id=None,
                            expiration_date=None, brand=None, department=None,
                            group=None, kpi=1, is_admin=False):
    request = current.request

    expiration = None
    if expiration_date:
        expiration = parser.parse(expiration_date)

    user_attributes = dict(brand=brand, department=department, userGroup=group,
                           KPI=kpi or 1)

    is_active = True
    if request.vars.is_active == '0':
        is_active = False

    # create user for existing domain
    user = create_user(email=email, domain_id=domain_id, first_name=first_name,
                       last_name=last_name, expiration=expiration,
                       is_active=is_active, is_admin=is_admin,
                       user_attributes=user_attributes,
                       set_registration_key=True)
    user_id = user['user_id']

    if user_attributes:
        current.db.user_attributes.insert(brand=user_attributes['brand'], userId=user_id,
                                          department=user_attributes['department'],
                                          userGroup=user_attributes['userGroup'],
                                          KPI=user_attributes['KPI'])

    # If this domain doesn't contain any templates, then create the sample templates
    get_or_create_default_email_templates(domain_id)

    return dict(id=user_id)


def check_if_user_exists(email, domain_id):
    # Get user if user exists
    domain_users = users_in_domain(domain_id)
    user = domain_users.find(lambda row: row.email == email).first()
    return True if user else False


def create_user(email, domain_id, first_name, last_name, expiration, is_active=True,
                is_admin=False, set_registration_key=False, user_attributes=None):
    db = current.db

    # Make new entry in user table
    registration_key = web2py_uuid() if set_registration_key else None
    hashed_password = hash_password(DEFAULT_USER_PASSWORD)
    user_id = _create_user(
        email,
        hashed_password,
        registration_key,
        domain_id,
        first_name,
        last_name,
        expiration,
        is_active=is_active,
        is_admin=is_admin
    )
    user = db.user(user_id)
    send_new_account_email(email, registration_key)
    return dict(user_id=user.id, email=email, registration_key=user.registration_key)


def is_current_user_admin(user_id=None):
    auth = current.auth
    return auth.has_membership(
        group_id=get_user_manager_group_id(),
        user_id=user_id) or auth.has_membership(
        group_id=get_customer_manager_group_id(), user_id=user_id)


def is_current_user_gettalent_admin(user_id=None):
    auth = current.auth
    return auth.has_membership(group_id=get_customer_manager_group_id(),
                               user_id=user_id)


def get_or_create_dice_user(email, first_name, last_name, dice_user_id, dice_company_id, access_token, refresh_token, dice_env='prod'):
    """
    Will notify admins if Dice user is auto-created. Also, will add in the diceUserId & diceCompanyId if it's not already there.

    :return: Row in user table
    :rtype: None | gluon.dal.Row
    """

    logger = current.logger
    # Try to locate the user in our DB by its diceUserId and email
    db = current.db
    user_row = db(db.user.diceUserId == dice_user_id).select().first() or db(db.user.email == email).select().first()
    if not user_row:
        # Get or create the user's domain
        domain = domain_from_dice_company_id(dice_company_id)
        is_auto_created_domain = False
        if not domain:
            dice_company_name = query_dice_company_id(dice_company_id=dice_company_id, dice_access_token=access_token,
                                                      dice_refresh_token=refresh_token, dice_env=dice_env)
            if not dice_company_name:
                logger.error("Tried to create domain for Dice user ID %s, but failed to query Company API", dice_user_id)
                return None
            domain_id = get_or_create_domain(dice_company_name, dice_company_id=dice_company_id)
            domain = domain_from_id(domain_id)
            current.logger.info("Auto-creating domain %s" % domain_id)
            email_notification_to_admins("Auto-creating domain %s (%s)" % (domain_id, dice_company_name), "Auto-creating domain")
            is_auto_created_domain = True

        # Create the user
        logger.info("Auto-creating Dice user %s (%s)", dice_user_id, email)
        user_id = _create_user(email=email, hashed_password=None, registration_key=None, domain_id=domain.id, first_name=first_name,
                              last_name=last_name, expiration=None, dice_user_id=dice_user_id, is_admin=is_auto_created_domain)
        user_row = user_from_id(user_id)
        email_notification_to_admins("Auto-creating user %s (%s)" % (user_id, email), "Auto-creating user")
    else:
        if not user_row.diceUserId:
            # Make sure user is Dice-connected
            current.logger.info("User %s was previously not Dice-connected. Will connect user with Dice ID %s", email, dice_user_id)
            user_row.update_record(diceUserId=dice_user_id)

        # Also make sure the domain is Dice-connected
        domain = domain_from_id(user_row.domainId)
        get_or_create_domain(domain.name, dice_company_id=dice_company_id)

    return user_row


def get_or_create_user(email, domain_id, first_name=None, last_name=None, expiration=None, is_active=True, is_admin=False,
                       set_registration_key=False, user_attributes=None):
    """

    :rtype: dict[str, int | str]
    """

    db = current.db

    # Get user if exists
    domain_users = users_in_domain(domain_id)
    user = domain_users.find(lambda row: row.email == email and row.domainId == domain_id).first()

    if not user:
        # Make new entry in user table
        registration_key = web2py_uuid() if set_registration_key else None
        hashed_password = hash_password(DEFAULT_USER_PASSWORD)
        user_id = _create_user(
            email,
            hashed_password,
            registration_key,
            domain_id,
            first_name,
            last_name,
            expiration,
            is_active=is_active,
            is_admin=is_admin
        )
        user = db.user(user_id)

        # Insert user's associated data & send welcome email
        # all_rating_tags = db(db.rating_tag.id >= 0).select()
        # generic_rating_tags = all_rating_tags.find(
        #     lambda rt: rt.description in ('Overall', 'Presentation', 'Communication Skills', 'Interests', 'Academic Experience', 'Work Experience'))
        # rating_tag_users = [{'ratingTagId': rt.id, 'userId': user_id} for rt in generic_rating_tags]
        # db.rating_tag_user.bulk_insert(rating_tag_users)

        send_new_account_email(email, registration_key)

    return dict(user_id=user.id, email=email, registration_key=user.registration_key)


def get_or_create_default_email_templates(domain_id):
    db = current.db
    import os

    sample_templates_folder = db(db.email_template_folder.domainId == domain_id)(db.email_template_folder.name == 'Sample Templates').select().first()

    if not sample_templates_folder:
        # Create the Sample Templates folder if it doesn't exist
        sample_template_folder_id = db.email_template_folder.insert(name='Sample Templates', domainId=domain_id, parentId=None, isImmutable=0)
        sample_templates_folder = db.email_template_folder(sample_template_folder_id)

    sample_templates = db(db.user_email_template.emailTemplateFolderId == sample_templates_folder.id).select()
    sample_template_names = [t.name for t in sample_templates]

    if ('Announcement' not in sample_template_names) and ('Intro' not in sample_template_names):
        # Create the sample templates if they don't exist
        get_talent_special_announcement = os.getcwd() + "/applications/web/static/getTalentSpecialAnnouncement.html"
        get_talent_special_announcement_str = open(get_talent_special_announcement).read()

        get_talent_intro = os.getcwd() + "/applications/web/static/getTalentIntro.html"
        get_talent_intro_str = open(get_talent_intro).read()

        admin_user = db(
            (db.user.domainId == domain_id) &
            (db.user.id == db.web_auth_membership.user_id) &
            (db.web_auth_membership.group_id == get_user_manager_group_id())
        ).select(db.user.ALL).first()

        if not admin_user:
            current.logger.warn("_get_or_create_default_email_templates: No admin user found for domain %s, using normal user instead", domain_id)
            admin_user = db(db.user.domainId == domain_id).select().first()

        db.user_email_template.insert(userId=admin_user.id, type='0', name='Announcement',
                                      emailBodyHtml=str(get_talent_special_announcement_str), emailBodyText='',
                                      emailTemplateFolderId=sample_templates_folder.id, isImmutable='0')
        db.user_email_template.insert(userId=admin_user.id, type='0', name='Intro',
                                      emailBodyHtml=str(get_talent_intro_str), emailBodyText='',
                                      emailTemplateFolderId=sample_templates_folder.id, isImmutable='0')
    return sample_templates_folder.id


def hash_password(password):
    return TALENT_CRYPT(password)[0]


def send_new_account_email(email, registration_key):
    new_user_email = current.response.render('email_templates/new_user.html',
                                             dict(email=email, registration_key=registration_key))
    from TalentSES import send_email

    send_email(source='"GetTalent Registration" <registration@gettalent.com>',
               subject='Setup Your New Account',
               body=new_user_email, to_addresses=[email], email_format='html')


def _get_auth_groups():
    db = current.db
    cache = current.cache
    return db(db.web_auth_group.id >= 0).select()


def get_customer_manager_group_id():
    return _get_auth_groups().find(lambda g: g.role == 'Customer Manager').first().id


def get_user_manager_group_id():
    return _get_auth_groups().find(lambda g: g.role == 'User Manager').first().id


def get_passive_user_group_id():
    return _get_auth_groups().find(lambda g: g.role == 'Passive User').first().id


def get_or_create_rating_custom_fields(domain_id):
    """
    Ratings are system defined custom fields and will be created at the time when domain is created.

    Add various rating fields, this rating custom field can be be used to search candidates based on their ratings provided.

    Will only create the CF Category & CFs if they don't exist for this domain.
    """
    db = current.db

    # Get the Rating custom_field_category. If it doesn't exist, create it and the default Rating CFs.
    existing_rating_cf_category = db(db.custom_field_category.domainId == domain_id)(db.custom_field_category.name == RATING_CATEGORY_NAME).select().first()
    if existing_rating_cf_category:
        rating_category_id = existing_rating_cf_category.id
    else:
        current.logger.info("Auto-creating rating CF category for domain %s", domain_id)
        rating_category_id = db.custom_field_category.insert(domainId=domain_id, name=RATING_CATEGORY_NAME)

        # Create the Rating custom_fields
        rows_dict = [{'domainId': domain_id, 'name': name, 'type': 'number', 'categoryId': rating_category_id} for name in RATING_FIELDS]
        current.logger.info("Auto-creating rating CFs %s for domain %s", rows_dict, domain_id)
        db.custom_field.bulk_insert(rows_dict)

    # Now fetch them all
    return db(db.custom_field.domainId == domain_id)(db.custom_field.categoryId == rating_category_id).select()


def add_or_update_ratings(candidate_id, rating_dict):
    """
    Add or update ratings custom field for candidates.
    :param candidate_id: Id of candidate whose rating is to be updated
    :param rating_dict: Dictionary containing customFieldId (of rating types) and its value (score of rating)
    :param candidate_current_custom_fields: All custom fields present for this candidate
    :return:
    """
    db = current.db
    candidate_current_custom_fields = db(db.candidate_custom_field.candidateId == candidate_id).select()

    for rating_field, rating_value in rating_dict.iteritems():
        candidate_custom_field_row = candidate_current_custom_fields.find(lambda row: row.customFieldId == rating_field).first()
        if candidate_custom_field_row:  # if rating_tag is already present update the value
            # Delete the row if rating is cleared (i.e. rating value is 0)
            if rating_value == '0':
                del db.candidate_custom_field[candidate_custom_field_row.id]
            # Else update the row with new value
            else:
                candidate_custom_field_row.update_record(value=rating_value)
        else:  # else insert a new row for rating_tag
            # Only insert if rating has some value other than 0. If no rating provided or rating cleared means 0.
            if rating_value != '0':
                db.candidate_custom_field.insert(candidateId=candidate_id, customFieldId=rating_field, value=rating_value)


def authenticate_user():
    """
    :return: User Row object or None, if auth fails
    """
    request = current.request

    # Check if user is logged in via current.auth (i.e. web2py cookie authentication)
    if current.auth and current.auth.user:
        return current.auth.user or None

    # Check if user is logged in via HTTP Basic Auth or CAS, if user_id and ticket are supplied
    if request.vars.user_id and request.vars.ticket:
        return _user_from_basic_auth("Basic %s" % base64.b64encode("%s:%s" % (request.vars.user_id, request.vars.ticket)))

    # Check If a trusted client wants to authenticate using a bearer token
    if request.env.http_authorization and 'bearer ' in request.env.http_authorization.lower():
        current.logger.info('A third party request is made to access gettalent resources using access_token: %s', request.env.http_authorization)
        access_token = request.env.http_authorization.lower().replace('bearer ', '').strip()
        user_id = verify_auth_service_access_token(access_token)
        if user_id:
            return current.db.user(user_id) or None

    # Otherwise, check session for auth & refresh tokens
    access_token = get_auth_service_access_token_from_session()
    refresh_token = get_auth_service_refresh_token_from_session()

    if access_token and refresh_token:
        # Refresh bearer token
        refresh_auth_service_access_token(refresh_token)
        access_token = get_auth_service_access_token_from_session()
        user_id = verify_auth_service_access_token(access_token) if access_token else None
        if user_id:
            return current.db.user(user_id) or None

    return None


def refresh_auth_service_access_token(refresh_token):
    """
    :param refresh_token: Resfresh token value
    """
    from datetime import datetime, timedelta
    token_expiry_time = get_auth_service_access_token_expiration_from_session()
    if refresh_token and token_expiry_time and token_expiry_time < datetime.utcnow():
        # Token has expired so refresh the token using Talent AuthService
        params = dict(grant_type="refresh_token", refresh_token=refresh_token)
        try:
            auth_service_token_response = requests.post(current.OAUTH_SERVER,
                                                        params=params, auth=(current.OAUTH_CLIENT_ID, current.OAUTH_CLIENT_SECRET)).json()
            if not (auth_service_token_response.get(u'access_token') and auth_service_token_response.get(u'refresh_token')):
                current.logger.error("authenticate_user: Either Access Token or Refresh Token is missing from response: %s", auth_service_token_response)
            else:
                store_auth_service_tokens_in_session(auth_service_token_response)
        except Exception as e:
            current.logger.exception("authenticate_user: Received exception, couldn't refresh Bearer Token with refresh token %s", refresh_token)


def verify_auth_service_access_token(access_token):
    """
    :param access_token: Access token value
    :return:  user_id if access_token is verified
    """

    from requests_oauthlib import OAuth2Session
    try:
        remote = OAuth2Session(token=dict(access_token=access_token))
        response = remote.get(current.OAUTH_SERVER_AUTHORIZE)
        if response.status_code == 200:
            user_id = response.json().get('user_id') or None
            current.logger.info('authenticate_user: Access granted to user %s with Authorization: %s', user_id, access_token)
            return user_id
        else:
            current.logger.warn('Access refused to a client with Authorization: %s', access_token)
            return None
    except Exception:
        current.logger.warn('Access refused to a client with Authorization: %s', access_token)
        return None


def store_auth_service_tokens_in_session(auth_service_token_response):
    """
    :param auth_service_token_response: The dict from AuthService containing access token, refresh token, and expiry.
    :type auth_service_token_response: dict[str, T]
    """
    current.session.auth_service_token_response = {u'access_token': auth_service_token_response.get(u'access_token'),
                                                   u'refresh_token': auth_service_token_response.get(u'refresh_token'),
                                                   # 10 seconds offset to compensate time required for refreshing the bearer token
                                                   u'expires_at': datetime.datetime.strptime(auth_service_token_response[u'expires_at'], "%d/%m/%Y %H:%M:%S") - datetime.timedelta(seconds=10)}


def get_auth_service_access_token_from_session():
    return current.session.auth_service_token_response and current.session.auth_service_token_response.get(u'access_token')


def get_auth_service_refresh_token_from_session():
    return current.session.auth_service_token_response and current.session.auth_service_token_response.get(u'refresh_token')


def get_auth_service_access_token_expiration_from_session():
    return current.session.auth_service_token_response and current.session.auth_service_token_response.get(u'expires_at')



def verify_user_scoped_role(user_id, role):
    try:
        role_verification_response = requests.get(current.OUTH_SERVICE_VERIFY_ROLES, params=dict(user_id=user_id, role=role))
        return role_verification_response.json().get('success') or False
    except Exception:
        current.logger.exception("Couldn't verify the user role")
        return False


def _user_from_basic_auth(basic_auth_str):  # Basic <b64 encoded user_id:ticket>
    db = current.db

    if not basic_auth_str:
        return None

    base64_encoded_user_id_password = basic_auth_str.split(' ')[1]
    user_id, ticket = base64.b64decode(base64_encoded_user_id_password).split(':')

    web_auth_cas_row = db(db.web_auth_cas.ticket == ticket)(db.web_auth_cas.user_id == user_id).select().first()
    if web_auth_cas_row:
        ticket_issue_time = web_auth_cas_row.created_on
        current_time = datetime.datetime.now()

        # ticket must be less than or equal to 1 day
        if (current_time - ticket_issue_time).days <= 1:
            return current.db.user(user_id)


def transfer_ownership_of_all_things_to_user(user_id, admin_user_id):
    db = current.db
    # Assign candidates to admin for that domain
    db(db.candidate.ownerUserId == user_id).update(ownerUserId=admin_user_id)
    # Assign user's smartlists to admin
    db(db.smart_list.userId == user_id).update(userId=admin_user_id)
    # Assign user's widgets to admin user
    db(db.widget_page.userId == user_id).update(userId=admin_user_id)
    # Assign user's email template id to admin user
    db(db.user_email_template.userId == user_id).update(userId=admin_user_id)
    # Assign user's Email Campaigns to admin user
    db(db.email_campaign.userId == user_id).update(userId=admin_user_id)


def get_domain_value(user, domain=None):
    if is_current_user_gettalent_admin(user_id=user.id) and domain:
        current.logger.info('get_domain_value: getTalent admin setting domain value: %s.', domain)
        domain = domain
    else:
        current.logger.info("get_domain_value: Did not receive domain; "
                            "setting domain to authenticated user's domain: %s.", domain)
        domain = user.domainId

    return domain


def _update_user(*args):
    """
    :rtype: gluon.dal.objects.Row
    """
    params = args[0]
    user_id = params.get('user_id')

    # Remove key-value-pairs if key's value is empty or None
    update_dict = dict((k, v) for k, v in params.iteritems() if v)

    # Remove user_id from update_dict
    del update_dict['user_id']

    # Update user's record with new inf
    user_row = current.db.user(user_id)
    user_row.update_record(**update_dict)

    return user_row


def get_users_domain_admin(requested_user):
    """
    Function caches all admin users from database and
    retrieves the admin of the requested user's domain who
    is not a getTalent admin

    It is assumed that each domain has at least 1 admin, AKA: user-manager

    :rtype: gluon.dal.objects.Row
    """
    db = current.db

    admin_id = get_user_manager_group_id()

    cache_admin_users = db(db.web_auth_membership.group_id == admin_id).select(
        db.web_auth_membership.user_id)
    admin_user_ids = [users['user_id'] for users in cache_admin_users]

    # Retrive admin of the requested-user's domain who is not a getTalent admin
    requested_users_domain_admin = db(
        db.user.id.belongs(admin_user_ids) &
        (db.user.domainId == requested_user.domainId)
    ).select().first()

    return requested_users_domain_admin








