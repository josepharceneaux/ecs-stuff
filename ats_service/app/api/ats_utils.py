"""
Utility functions for the ATS service.
"""

__author__ = 'Joseph Arceneaux'

import datetime

from enum import Enum


if __name__ == 'ats_service.app.api.ats_utils':
    # Imports for the web app.
    from ats_service.common.models.ats import db, ATS, ATSAccount, ATSCredential, ATSCandidate, ATSCandidateProfile
    from ats_service.common.models.candidate import Candidate
    from ats_service.common.models.user import User
    from ats_service.common.utils.validators import format_phone_number
    from ats_service.common.error_handling import *
    from ats_service.ats.workday import Workday
else:
    # Imports for the refresh script
    from common.models.ats import db, ATS, ATSAccount, ATSCredential, ATSCandidate, ATSCandidateProfile
    from common.models.candidate import Candidate
    from common.models.user import User
    from common.utils.validators import format_phone_number
    from common.error_handling import *
    from ats.workday import Workday


ATS_ACCOUNT_FIELDS = ['ats_name', 'ats_homepage', 'ats_login', 'ats_auth_type', 'ats_id', 'ats_credentials']
ATS_CANDIDATE_FIELDS = ['ats_remote_id', 'profile_json']

# ATS we support
WORKDAY = 'Workday'
GREENDAY = 'Greenday'
ATS_SET = {WORKDAY, GREENDAY}

# Constructors
ATS_CONSTRUCTORS = { WORKDAY : Workday }


def validate_ats_account_data(data):
    """
    Verify that POST data contains all required fields for dealing with an ATS account.

    :param dict data: keys and their values
    :rtype: None
    """
    missing_fields = [field for field in ATS_ACCOUNT_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise InvalidUsage('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields))

    if data['ats_name'] not in ATS_SET:
        raise UnprocessableEntity("Invalid data", additional_error_info=dict(unsupported_ats=data['ats_name']))


def invalid_account_fields_check(data):
    """
    Verify that data contains only valid ATS account fields.

    :param dict data: keys and their values
    :rtype: None
    """
    field_names = data.keys()
    invalid_fields = [name for name in field_names if name not in ATS_ACCOUNT_FIELDS]
    if invalid_fields:
        raise UnprocessableEntity("Invalid data", additional_error_info=dict(missing_fields=invalid_fields))


def validate_ats_candidate_data(data):
    # type: (object) -> object
    """
    Verify that POST data contains all required fields for dealing with an ATS candidate.

    :param dict data: keys and their values
    :return: None, or throws an exception.
    """
    missing_fields = [field for field in ATS_CANDIDATE_FIELDS if field not in data or not data[field]]
    if missing_fields:
        raise InvalidUsage('Some required fields are missing', additional_error_info=dict(missing_fields=missing_fields))


def new_ats(data):
    """
    Register a new Applicant Tracking System.

    :param dict data: keys and values describing the ATS.
    :rtype: ATS
    """
    ats = ATS(name=data['ats_name'], homepage_url=data['ats_homepage'], login_url=data['ats_login'], auth_type=data['ats_auth_type'])
    ats.save()
    return ats


def new_ats_account(user_id, ats_id, data):
    """
    Register an ATS account for a user.

    :param int user_id: id of the user to associate the account with.
    :param int ats_id: id of the ATS system.
    :param dict data: keys and values describing the account.
    :rtype: ATS
    """
    # Create account and credential entries
    account = ATSAccount(active=True, ats_id=ats_id, user_id=user_id, ats_credential_id=0)
    account.save()
    credentials = ATSCredential(ats_account_id=0, auth_type=data['ats_auth_type'], credentials_json=data['ats_credentials'])
    credentials.save()

    # Now make the two rows point to each other
    update_dict = {'ats_credential_id': credentials.id}
    account.update(**update_dict)
    update_dict = {'ats_account_id': account.id}
    credentials.update(**update_dict)
    update_dict = {'ats_enabled': True}
    User.get(user_id).update(**update_dict)

    return account


def update_ats_account(account_id, new_data):
    """
    Update the values of an ATS account.

    :param int account_id: primary key of the account.
    :param dict new_data: New values for the account.
    :rtype: None
    """
    # Search for the account, complain if it doesn't exist
    account = ATSAccount.get(account_id)
    if not account:
        raise UnprocessableEntity("Invalid ats account id", additional_error_info=dict(id=account_id))
    ats = ATS.get(account.ats_id)
    if not ats:
        raise UnprocessableEntity("Invalid ats id", additional_error_info=dict(id=account.ats_id))

    # Update the ATS info
    update_dict = {}
    if 'ats_name' in new_data:
        update_dict['name'] = new_data['ats_name']
    if 'ats_homepage' in new_data:
        update_dict['homepage_url'] = new_data['ats_homepage']
    if 'ats_login' in new_data:
        update_dict['login_url'] = new_data['ats_login']
    if 'ats_auth_type' in new_data:
        update_dict['auth_type'] = new_data['ats_auth_type']
    if len(update_dict) > 0:
        ats.update(**update_dict)

    update_dict = {}
    now = datetime.datetime.utcnow()
    update_dict = {'updated_at' : now}
    if 'active' in new_data:
        if new_data['active'] == "False":
            update_dict['active'] = False
        else:
            update_dict['active'] = True

        account.update(**update_dict)

    # If they're changing credentials, find those. Presumably auth_type won't change.
    if 'ats_credentials' in new_data:
        credentials = ATSCredential.get(account.ats_credential_id)
        update_dict = {'credentials_json' : new_data['ats_credentials']}
        credentials.update(**update_dict)


def delete_ats_account(user_id, ats_account_id):
    """
    Remove an ATS account and all of its candidates.

    :param int ats_account_id: id of the ATS account.
    :rtype: None
    """
    # First, verify the user and account
    account = ATSAccount.get(ats_account_id)
    if not account:
        raise NotFoundError('delete_ats_account: No such account {}'.format(ats_account_id))

    user = User.get(user_id)
    if not user:
        raise NotFoundError('delete_ats_account: No such user {}'.format(user_id))

    # Next remove all candidates and candidate attributes from the account
    candidate_list = ATSCandidate.query.filter(ATSCandidate.ats_account_id == ats_account_id).all()
    for candidate in candidate_list:
        profile = ATSCandidateProfile.get(candidate.profile_id)
        ATSCandidateProfile.delete(profile)

    # Then remove the account credentials
    credentials = ATSCredential.get(account.ats_credential_id)
    ATSCredential.delete(credentials)

    # Remove the account
    ATSAccount.delete(account)

    # If this is the only ATS account for this user, mark the user as not ATS enabled
    all_accounts = ATSAccount.query.filter(ATSAccount.user_id == user_id).all()
    if not all_accounts:
        update_dict = {'ats_enabled': False}
        User.query.filter(User.id == user_id).update(update_dict)
        db.session.commit()


def new_ats_candidate(account_id, data):
    """
    Register an ATS candidate with an ATS account.

    :param obj account: an ATS account object.
    :param dict data: keys and values describing the candidate.
    :rtype: ATSCandidate
    """
    gt_candidate_id = None
    if 'gt_candidate_id' in data:
        gt_candidate_id = data.get('gt_candidate_id', None)
    account = ATSAccount.get(account_id)
    if not account:
        raise InvalidUsage("ATS account {} not found.".format(account_id))
    profile = ATSCandidateProfile(active=True, profile_json=data['profile_json'], ats_id=account.ats_id)
    profile.save()
    candidate = ATSCandidate(ats_account_id=account.id, ats_remote_id=data['ats_remote_id'], gt_candidate_id=gt_candidate_id, profile_id=profile.id)
    if 'ats_table_id' in data:
        candidate.ats_table_id = data.get('ats_table_id', None)
    candidate.save()

    update_dict = {}
    now = datetime.datetime.utcnow()
    update_dict = {'updated_at' : now}
    account.update(**update_dict)

    return candidate
 

def delete_ats_candidate(candidate_id):
    """
    Remove an ATS candidate from the database.

    :param int candidate_id: The id of the candidate.
    :rtype: None
    """
    candidate = ATSCandidate.get(candidate_id)
    if not candidate:
        raise InvalidUsage('delete_ats_candidate: No such candidate {}'.format(candidate_id))

    profile = ATSCandidateProfile.get(candidate.profile_id)
    if profile:
        ATSCandidateProfile.delete(profile)

    account = ATSAccount.get(candidate.ats_account_id)
    if not account:
        raise InvalidUsage("ATS account {} not found.".format(candidate.ats_account_id))
    now = datetime.datetime.utcnow()
    update_dict = {'updated_at' : now}
    account.update(**update_dict)


def update_ats_candidate(account_id, candidate_id, new_data):
    """
    Update the profile of an ATS candidate.

    :param int account_id: primary key of the account the candidate belongs to.
    :param int candidate_id: primary key of the candidate.
    :param dict new_data: values to update for the candidate.
    :rtype: None
    """
    if 'profile_json' not in new_data:
        raise InvalidUsage("profile_json not found.")

    # Validate ATS Account
    account = ATSAccount.get(account_id)
    if not account:
        raise InvalidUsage("ATS account {} not found.".format(account_id))

    # Validate candidate id
    candidate = ATSCandidate.get(candidate_id)
    if not candidate:
        raise UnprocessableEntity("Invalid candidate id", additional_error_info=dict(id=account.candidate_id))

    # Validate profile id
    profile = ATSCandidateProfile.get(candidate.profile_id)
    if not profile:
        raise UnprocessableEntity("Invalid candidate profile id", additional_error_info=dict(id=candidate.profile_id))

    if 'ats_table_id' in new_data:
        candidate.ats_table_id = new_data.get('ats_table_id', None)

    now = datetime.datetime.utcnow()
    update_dict = {'profile_json' : new_data['profile_json'], 'updated_at' : now}
    profile.update(**update_dict)

    update_dict = {'updated_at' : now}
    candidate.update(**update_dict)
    account.update(**update_dict)

    return candidate


def link_ats_candidate(gt_candidate_id, ats_candidate_id):
    """
    Mark an ATS candidate as being the same as a getTalent candidate.

    :param int gt_candidate_id: id of the GT candidate.
    :param int ats_candidate_id: id of the ATS candidate.
    :rtype: None
    """
    gt_candidate = Candidate.get(gt_candidate_id)
    if not gt_candidate:
        raise InvalidUsage("getTalent candidate id {} not found".format(gt_candidate_id))

    ats_candidate = ATSCandidate.get(ats_candidate_id)
    if not ats_candidate:
        raise InvalidUsage("ATS candidate id {} not found.".format(ats_candidate_id))

    update_dict = {'gt_candidate_id': gt_candidate_id}
    ats_candidate.update(**update_dict)


def unlink_ats_candidate(gt_candidate_id, ats_candidate_id):
    """
    Remove the association of a GT candidate with an ATS candidate.

    :param int gt_candidate_id: id of the GT candidate.
    :param int ats_candidate_id: id of the ATS candidate.
    :rtype: None
    """
    gt_candidate = Candidate.get(gt_candidate_id)
    if not gt_candidate:
        raise InvalidUsage("Candidate id {} not found".format(gt_candidate_id))

    ats_candidate = ATSCandidate.get(ats_candidate_id)
    if not ats_candidate:
        raise InvalidUsage("ATS Candidate id {} not found".format(ats_candidate_id))

    update_dict = {'gt_candidate_id': None}
    ats_candidate.update(**update_dict)


def fetch_auth_data(account_id):
    """
    Return the values needed to authenticate to an ATS account.

    :param int account_id: Primary key of the account.
    :rtype string: ATS name.
    :rtype string: Login URL.
    :rtype: tuple[str] | tuple[str] | tuple[int] | tuple[ATSCredential]:
    """
    # Validate ATS Account
    account = ATSAccount.get(account_id)
    if not account:
        raise InvalidUsage("ATS account {} not found.".format(account_id))

    if not account.active:
        return None, None, None, None

    ats = ATS.get(account.ats_id)
    if not ats:
        raise UnprocessableEntity("Invalid ats id", additional_error_info=dict(id=account.ats_id))

    credentials = ATSCredential.get(account.ats_credential_id)
    if not credentials:
        raise UnprocessableEntity("No credentials for account", additional_error_info=dict(id=account.ats_id))

    return ats.name, ats.login_url, account.user_id, credentials


def create_ats_object(logger, ats_name, url, user_id, credentials):
    """
    Authenticate to the specified ATS
    :param string ats_name: ATS name.
    :param string url: Login URL.
    :param string user_id: User id.
    :param string credentials: Authentication credentials.
    """
    if ats_name not in ATS_SET:
        raise UnprocessableEntity("Invalid data", additional_error_info=dict(unsupported_ats=data['ats_name']))

    return ATS_CONSTRUCTORS[ats_name](logger, ats_name, url, user_id, credentials)


def emails_match(gt_candidate, ats_candidate):
    """
    Determine if there are matching email addresses between a GT candidate and a Workday individual.
    Workday individuals have only one, but this returns a list so that all ATS may have the same method signature.
    :param Candidate gt_candidate: getTalent candidate.
    :param ATSCandidate ats_candidate: Workday individual.
    :rtype boolean:
    """
    if gt_candidate.is_archived:
        return False

    # Get the ATS candidate email address with an ATS-specific static method
    ats_email_list = ATS_CONSTRUCTORS[ATSAccount.get(ats_candidate.ats_id).name].get_individual_contact_email_addresses(ats_candidate)
    if not ats_email_list:
        return False

    # Compare to GT candidate email address(es)
    if not gt_candidate.emails:
        return False

    # Compare. This makes a 4-deep for loop, but we expect the lists to be very small. For Workday, there'll be only one email address.
    for gt_email in candidate.emails:
        for ats_email in ats_email_list:
            if gt_email == ats_email:
                return True

    return False


def normalized_phones_match(gt_phone_list, ats_phone_list):
    """
    """
    # Compare. This makes a 4-deep for loop, but we expect the lists to be very small. For Workday, there'll be only one email address.
    for gt_phone in gt_phone_list:
        try:
            normalized_gt_phone = format_phone_number(gt_phone)
        except:
            continue

        for ats_phone in ats_phone_list:
            try:
                normalized_ats_phone = format_phone_number(ats_phone)
            except:
                continue

            if normalized_gt_phone == normalized_ats_phone:
                return True

    return False


def phones_match(gt_candidate, ats_candidate):
    """
    Determine if there are matching phone numbers between a GT candidate and a Workday individual.
    Workday indidviduals have only one, but this returns a list so that all ATS may have the same method signature.
    :param Candidate gt_candidate: getTalent candidate.
    :param ATSCandidate ats_candidate: Workday individual.
    :rtype boolean:
    """
    if gt_candidate.is_archived:
        return False

    # Get the ATS candidate email address with an ATS-specific static method
    ats_phone_list = ATS_CONSTRUCTORS[ATSAccount.get(ats_candidate.ats_id).name].get_individual_contact_phone_numbers(ats_candidate)
    if not ats_phone_list:
        return False

    # Compare to GT candidate email address(es)
    if not gt_candidate.phones:
        return False

    return normalized_phones_match(candidate.phones, ats_phone_list)


def emails_and_phones_match(gt_candidate, ats_candidate):
    """
    Determine if there are matching email addresses and phone numbers between a GT candidate and a Workday individual.
    Workday indidviduals have only one, but this returns a list so that all ATS may have the same method signature.
    :param Candidate gt_candidate: getTalent candidate.
    :param ATSCandidate ats_candidate: Workday individual.
    :rtype boolean:
    """
    if gt_candidate.is_archived:
        return False

    # Get the ATS candidate email address with an ATS-specific static method
    ats_phone_list = ATS_CONSTRUCTORS[ATSAccount.get(ats_candidate.ats_id).name].get_individual_contact_phone_numbers(ats_candidate)
    if not ats_phone_list:
        return False

    # Compare to GT candidate email address(es)
    if not gt_candidate.phones:
        return False

    # Get the ATS candidate email address with an ATS-specific static method
    ats_email_list = ATS_CONSTRUCTORS[ATSAccount.get(ats_candidate.ats_id).name].get_individual_contact_email_addresses(ats_candidate)
    if not ats_email_list:
        return False

    # Compare to GT candidate email address(es)
    if not gt_candidate.emails:
        return False

    # Compare emails.
    for gt_email in candidate.emails:
        for ats_email in ats_email_list:
            if gt_email == ats_email:
                email_match = True

    # Compare phones.
    phone_match = normalized_phones_match(candidate.phones, ats_phone_list)

    return email_match and phone_match


def emails_or_phones_match(gt_candidate, ats_candidate):
    """
    Determine if there are matching email addresses or phone numbers between a GT candidate and a Workday individual.
    Workday indidviduals have only one, but this returns a list so that all ATS may have the same method signature.
    :param Candidate gt_candidate: getTalent candidate.
    :param ATSCandidate ats_candidate: Workday individual.
    :rtype boolean:
    """
    if gt_candidate.is_archived:
        return False

    # Get the ATS candidate email address with an ATS-specific static method
    ats_phone_list = ATS_CONSTRUCTORS[ATSAccount.get(ats_candidate.ats_id).name].get_individual_contact_phone_numbers(ats_candidate)
    if not ats_phone_list:
        return False

    # Compare to GT candidate email address(es)
    if not gt_candidate.phones:
        return False

    # Get the ATS candidate email address with an ATS-specific static method
    ats_email_list = ATS_CONSTRUCTORS[ATSAccount.get(ats_candidate.ats_id).name].get_individual_contact_email_addresses(ats_candidate)
    if not ats_email_list:
        return False

    # Compare to GT candidate email address(es)
    if not gt_candidate.emails:
        return False

    # Compare emails.
    for gt_email in candidate.emails:
        for ats_email in ats_email_list:
            if gt_email == ats_email:
                return True

    # Compare phones.
    return normalized_phones_match(candidate.phones, ats_phone_list)


MATCH_DICT = { u'email' : emails_match, u'phone' : phones_match,
               u'email-and-phone' : emails_and_phones_match,
               u'email-or-phone' : emails_or_phones_match }


def match_ats_and_gt_candidates(logger, account_id, method, link=False):
    """
    Search for getTalent condidates which appear to match ATS candidates using a particular method.

    :param object logger: object to use for logging.
    :param int account_id: ATS account to search within.
    :param string method: matching technique to use.
    :param boolean link: Whether to link the candidates matched or not.
    :rtype int: Number of matches found.
    """
    if method not in MATCH_DICT:
        raise UnprocessableEntity("match_ats_and_gt_candidates: Invalid match method", additional_error_info=dict(unsupported_method=method))

    match_method = MATCH_DICT[method]

    account = ATSAccount.get(account_id)
    if not account:
        raise NotFoundError('ATS Account id not found', additional_error_info=dict(account_id=account_id))

    # Now get the user that owns this account
    user = User.get(account.user_id)
    # Get all candidates from user's domain
    gt_candidate_list = db.session.query(Candidate).join(User).filter(User.domain_id == user.domain_id).all()
    # Get a list of our ATS candidates
    ats_candidate_list = ATSCandidate.get_all(account_id)

    matches = 0
    for gt_candidate in gt_candidate_list:
        for ats_candidate in ats_candidate_list:
            if match_method(gt_candidate, ats_candidate):
                matches += 1
                if link:
                    link_ats_candidate(gt_candidate.id, ats_candidate.id)

    return matches
