"""
"""


from ats_service.common.models.ats import db, ATS, ATSAccount, ATSCredential
from ats_service.common.models.user import User

from ats_service.common.error_handling import InternalServerError, ResourceNotFound, ForbiddenError, InvalidUsage


ATS_ACCOUNT_FIELDS = ['ats_name', 'ats_homepage', 'ats_login', 'ats_auth_type', 'ats_id', 'ats_credentials']


def validate_ats_account_data(data):
    """
    """
    missing_fields = [field for field in ATS_ACCOUNT_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise InvalidUsage('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields),
                           error_code=CampaignException.MISSING_REQUIRED_FIELD)

def new_ats(data):
    """
    """
    ats = ATS(name=data['ats_name'], homepage_url=data['ats_homepage'], login_url=data['ats_login'], auth_type=data['ats_auth_type'])
    db.session.add(ats)
    db.session.commit()
    return ats

def new_ats_account(user_id, ats_id, data):
    """
    """
    # Create account and credential entries
    account = ATSAccount(active=True, ats_id=ats_id, user_id=user_id, ats_credential_id=0)
    db.session.add(account)
    credentials = ATSCredential(ats_account_id=0, auth_type=data['ats_auth_type'], credentials_json=data['ats_credentials'])
    db.session.add(credentials)
    db.session.commit()

    # Now make the two rows point to each other
    update_dict = { 'ats_credential_id': credentials.id }
    ATSAccount.query.filter(ATSAccount.id == account.id).update(update_dict)
    update_dict = { 'ats_account_id': account.id }
    ATSCredential.query.filter(ATSCredential.id == credentials.id).update(update_dict)
    db.session.commit()

    return account
