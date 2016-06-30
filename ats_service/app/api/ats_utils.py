"""
"""


from ats_service.common.models.ats import ATS, ATSAccount, ATSCredential
from ats_service.common.models.user import User

from ats_service.common.error_handling import InternalServerError, ResourceNotFound, ForbiddenError, InvalidUsage


ATS_ACCOUNT_FIELDS = ['ats_name', 'ats_homepage', 'ats_login', 'ats_auth_type', 'ats_credentials']

def validate_ats_account_data(data):
    """
    """
    missing_fields = [field for field in ATS_ACCOUNT_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise InvalidUsage('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields),
                           error_code=CampaignException.MISSING_REQUIRED_FIELD)

def find_ats_account(user_id, ats_name):
    """
    """
    # See if user has ATS enabled
    # user = User.query.filter_by(id=user_id).first()

    accounts = ATSAccount.query.filter_by(user_id=user_id)
    if len(accounts) > 0:
        for a in accounts:
            ats = ATS.query.filter_by(name=ats_name)
            if ats:
                return a
