__author__ = 'ufarooqi'
from flask import render_template
from user_service.common.utils.amazon_ses import send_email
from user_service.common.models.user import db, Domain, User, UserScopedRoles
from werkzeug.security import generate_password_hash, gen_salt


def get_or_create_domain(name, usage_limitation=-1, organization_id=1, expiration=None, default_culture_id=1, dice_company_id=None):
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
                        default_culture_id=default_culture_id, dice_company_id=dice_company_id, expiration=expiration)
        db.session.add(domain)
        db.session.commit()

        # get_or_create_rating_custom_fields(domain_id)
        return domain.id


def check_if_user_exists(email, domain_id):
    # Get user if user exists
    domain_users = User.query.filter_by(domain_id=domain_id).all()
    user = domain_users.find(lambda domain_user: domain_user.email == email).first()
    return True if user else False


def create_user_for_company(first_name, last_name, email, domain_id=None, expiration_date=None, is_admin=False, phone="",
                            is_domain_admin=False, dice_user_id=None):

    from dateutil import parser
    expiration = None
    if expiration_date:
        expiration = parser.parse(expiration_date)

    # create user for existing domain
    user = create_user(email=email, domain_id=domain_id, first_name=first_name, last_name=last_name, phone=phone,
                       expiration=expiration, is_admin=is_admin, is_domain_admin=is_domain_admin,
                       dice_user_id=dice_user_id)

    # TODO: If this domain doesn't contain any templates, then create the sample templates
    # get_or_create_default_email_templates(domain_id)

    return user.id


def create_user(email, domain_id, first_name, last_name, expiration, is_admin=False, is_domain_admin=False, phone="",
                dice_user_id=None):

    temp_password = gen_salt(20)
    hashed_password = generate_password_hash(temp_password, method='pbkdf2:sha512')

    # Make new entry in user table
    user = User(email=email, domain_id=domain_id, first_name=first_name, last_name=last_name, expiration=expiration,
                dice_user_id=dice_user_id, password=hashed_password, phone=phone)

    db.session.add(user)
    db.session.commit()

    # TODO: Make new widget_page if first user in domain
    # TODO: Add activity

    # Adding ADMIN or DOMAIN_ADMIN roles to newly created user

    if is_admin:
        UserScopedRoles.add_roles(user.id, True, ['ADMIN'])
    if is_domain_admin:
        UserScopedRoles.add_roles(user.id, True, ['DOMAIN_ADMIN'])

    send_new_account_email(email, temp_password)

    return user


def send_new_account_email(email, temp_password):
    new_user_email = render_template('new_user.html', email=email, password=temp_password)
    send_email(source='"GetTalent Registration" <registration@gettalent.com>',
               subject='Setup Your New Account',
               body=new_user_email, to_addresses=[email], email_format='html')
