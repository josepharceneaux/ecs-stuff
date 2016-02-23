__author__ = 'ufarooqi'
from flask import render_template
from werkzeug.security import gen_salt

from user_service.common.error_handling import InvalidUsage
from user_service.common.models.misc import EmailTemplateFolder, UserEmailTemplate
from user_service.common.models.user import db, Domain, User, UserGroup
from user_service.common.utils.amazon_ses import send_email
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
                            dice_user_id=None, thumbnail_url='', user_group_id=None):

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
                       user_group_id=user_group_id)

    return user.id


def get_or_create_default_email_templates(domain_id, admin_user_id):

    sample_templates_folder = EmailTemplateFolder.query.filter(EmailTemplateFolder.domain_id == domain_id,
                                                               EmailTemplateFolder.name == 'Sample Templates').first()

    if not sample_templates_folder:
        # Create the Sample Templates folder if it doesn't exist
        sample_templates_folder = EmailTemplateFolder(name='Sample Templates', domain_id=domain_id, parent_id=None,
                                                      is_immutable=0)
        db.session.add(sample_templates_folder)
        db.session.commit()

    sample_templates = UserEmailTemplate.query.filter(UserEmailTemplate.email_template_folder_id == sample_templates_folder.id)
    sample_template_names = [t.name for t in sample_templates]

    if ('Announcement' not in sample_template_names) and ('Intro' not in sample_template_names):
        # Create the sample templates if they don't exist
        get_talent_special_announcement = render_template('getTalentSpecialAnnouncement.html')
        get_talent_intro = render_template('getTalentIntro.html')

        announcement_template = UserEmailTemplate(user_id=admin_user_id, type='0', name='Announcement',
                                                  email_body_html=get_talent_special_announcement, email_body_text='',
                                                  email_template_folder_id=sample_templates_folder.id, is_immutable='0')

        intro_template = UserEmailTemplate(user_id=admin_user_id, type='0', name='Intro',
                                           email_body_html=get_talent_intro, email_body_text='',
                                           email_template_folder_id=sample_templates_folder.id, is_immutable='0')

        db.session.add(announcement_template)
        db.session.add(intro_template)
        db.session.commit()

    return sample_templates_folder.id


def create_user(email, domain_id, first_name, last_name, expiration, phone="", dice_user_id=None,
                thumbnail_url='', user_group_id=None):

    temp_password = gen_salt(20)
    hashed_password = gettalent_generate_password_hash(temp_password)

    # Get user's group ID
    if not user_group_id:
        user_groups = UserGroup.all_groups_of_domain(domain_id=domain_id)
        if user_groups:  # TODO: this shouldn't be necessary since each domain must belong to a user_group
            user_group_id = user_groups[0].id

    # Make new entry in user table
    user = User(email=email, domain_id=domain_id, first_name=first_name, last_name=last_name, expiration=expiration,
                dice_user_id=dice_user_id, password=hashed_password, phone=phone, thumbnail_url=thumbnail_url,
                user_group_id=user_group_id)

    db.session.add(user)
    db.session.commit()

    # TODO: Make new widget_page if first user in domain
    # TODO: Add activity

    send_new_account_email(email, temp_password)

    return user


def send_new_account_email(email, temp_password):
    new_user_email = render_template('new_user.html', email=email, password=temp_password)
    send_email(source='"getTalent Registration" <registration@gettalent.com>',
               subject='Setup Your New Account',
               body=new_user_email, to_addresses=[email], email_format='html')


def send_reset_password_email(email, name, reset_password_url, six_digit_token):
    new_user_email = render_template('reset_password.html', email=email, name=name, six_digit_token=six_digit_token,
                                     reset_password_url=reset_password_url)
    send_email(source='"getTalent Registration" <registration@gettalent.com>',
               subject='getTalent password reset',
               body=new_user_email, to_addresses=[email], email_format='html')
