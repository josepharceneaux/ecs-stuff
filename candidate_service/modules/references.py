"""
This file contains functions for candidate reference(s) CRUD operations
"""
# Models
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import (
    Candidate, CandidateReference, ReferenceWebAddress, EmailLabel, PhoneLabel
)
from candidate_service.common.models.associations import ReferenceEmail, ReferencePhone

# Handy functions
from candidate_service.common.utils.handy_functions import purge_dict

# Common validators
from candidate_service.common.utils.validators import format_phone_number

# Error handling
from candidate_service.common.error_handling import InvalidUsage, ForbiddenError
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


def get_references(candidate):
    """
    Function will return a list of candidate's references
    :type candidate:  Candidate
    :rtype:  list[dict]
    """
    return_list = []  # Aggregate all of candidate's references' information
    for reference in candidate.references:
        reference_id = reference.id
        return_dict = dict(
            id=reference_id,
            name=reference.person_name,
            position_title=reference.position_title,
            comments=reference.comments,
            reference_email=get_reference_emails(reference_id),
            reference_phone=get_reference_phones(reference_id),
            reference_web_address=get_reference_web_addresses(reference_id)
        )
        # Remove keys with empty values and strip each value
        return_dict = purge_dict(dictionary=return_dict, strip=False)
        return_list.append(return_dict)

    return return_list


def get_reference_emails(reference_id):
    """
    Function will return candidate's reference's email information
    :type reference_id:  int|long
    :rtype:  dict | None
    """
    reference_email = ReferenceEmail.get_by_reference_id(reference_id)
    if reference_email:
        return dict(label=EmailLabel.get_description_from_id(reference_email.email_label_id),
                    is_default=reference_email.is_default,
                    address=reference_email.value)


def get_reference_phones(reference_id):
    """
    Function will return candidate's reference's phone information
    :type reference_id:  int|long
    :rtype:  dict | None
    """
    reference_phone = ReferencePhone.get_by_reference_id(reference_id)
    if reference_phone:
        return dict(label=PhoneLabel.get_description_from_id(reference_phone.phone_label_id),
                    is_default=reference_phone.is_default,
                    value=reference_phone.value,
                    extension=reference_phone.extension)


def get_reference_web_addresses(reference_id):
    """
    Function will return candidate's reference's web address information
    :type reference_id:  int|long
    :rtype:  dict | None
    """
    reference_web_address = ReferenceWebAddress.get_by_reference_id(reference_id)
    if reference_web_address:
        return dict(id=reference_web_address.id,
                    url=reference_web_address.url,
                    description=reference_web_address.description)


def create_or_update_references(candidate_id, references, is_creating=False,
                                is_updating=False, reference_id_from_url=None):
    """
    Function will insert candidate's references' information into db.
    References' information must include: person_name and comments.
    References' information may include: reference-email dict & reference-phone dict.
    Empty data will not be added to db
    Duplicate records will not be added to db
    :type candidate_id: int|long
    :type references:  list[dict]
    :type is_creating: bool
    :type is_updating: bool
    :type reference_id_from_url: int | long
    :rtype:  list[int]
    """
    created_or_updated_reference_ids = []
    for reference in references:

        person_name = (reference.get('name') or '').strip()
        position_title = (reference.get('position_title') or '').strip()
        comments = (reference.get('comments') or '').strip()

        candidate_reference_dict = dict(
            person_name=person_name,
            position_title=position_title,
            comments=comments
        )
        # Strip each value & remove keys with empty values
        candidate_reference_dict = purge_dict(candidate_reference_dict, strip=False)

        # Prevent inserting empty records in db
        if not candidate_reference_dict:
            continue

        reference_id = reference_id_from_url or reference.get('id')
        if not reference_id and is_updating:
            raise InvalidUsage("Reference ID is required for updating", custom_error.INVALID_USAGE)

        candidate_reference_dict.update(resume_id=candidate_id, candidate_id=candidate_id)

        if is_creating:  # Add
            reference_id = add_reference(candidate_id, candidate_reference_dict)
        elif is_updating:  # Update
            update_reference(candidate_id, reference_id, candidate_reference_dict)

        reference_email = reference.get('reference_email')
        reference_phone = reference.get('reference_phone')
        reference_web_address = reference.get('reference_web_address')

        if reference_email:  # add reference's email info
            default_label = EmailLabel.PRIMARY_DESCRIPTION
            email_label = default_label if not reference_email.get('label') else reference_email[
                'label'].strip().title()
            value = reference_email['address'].strip() if reference_email.get('address') else None
            reference_email_dict = dict(
                email_label_id=EmailLabel.email_label_id_from_email_label(email_label) if value else None,
                is_default=reference_email.get('is_default') or True if value else None,
                value=value
            )
            # Remove keys with empty values
            reference_email_dict = purge_dict(reference_email_dict, strip=False)

            if reference_email_dict and is_creating:  # Add
                add_reference_email(reference_id, reference_email_dict)
            elif reference_email_dict and is_updating:  # Update
                update_reference_email(reference_id, reference_email_dict)

        if reference_phone:  # add reference's phone info if provided
            default_label = PhoneLabel.DEFAULT_LABEL
            phone_label = default_label if not reference_phone.get('label') else reference_phone[
                'label'].strip().title()
            value = reference_phone['value'].strip() if reference_phone.get('value') else None
            phone_number_dict = format_phone_number(value) if value else None
            reference_phone_dict = dict(
                phone_label_id=PhoneLabel.phone_label_id_from_phone_label(phone_label) if phone_number_dict else None,
                is_default=reference_phone.get('is_default') or True if phone_number_dict else None,
                value=phone_number_dict.get('formatted_number') if phone_number_dict else None,
                extension=phone_number_dict.get('extension') if phone_number_dict else None
            )
            # Remove keys with empty values
            reference_phone_dict = purge_dict(reference_phone_dict, strip=False)

            if reference_phone_dict and is_creating:  # Add
                add_reference_phone(reference_id, reference_phone_dict)
            elif reference_phone_dict and is_updating:  # Update
                update_reference_phone(reference_id, reference_phone_dict)

        if reference_web_address:
            reference_web_address_dict = dict(
                url=reference_web_address.get('url'),
                description=reference_web_address.get('description'),
            )
            # Remove keys with empty values & strip each value
            reference_web_address_dict = purge_dict(reference_web_address_dict)

            if reference_web_address_dict and is_creating:  # Add
                add_reference_web_address(reference_id, reference_web_address_dict)
            elif reference_web_address_dict and is_updating:  # Update
                update_reference_web_address(reference_id, reference_web_address_dict)

        db.session.commit()  # Commit transactions to db
        created_or_updated_reference_ids.append(reference_id)

    return created_or_updated_reference_ids


def add_reference(candidate_id, reference_dict):
    """
    Function will insert a record in CandidateReference.
    Function will check db to prevent adding duplicate records.
    :rtype  int | None
    """
    reference_name = reference_dict.get('person_name')
    if not reference_name:
        raise InvalidUsage("Reference's name is required", custom_error.INVALID_USAGE)

    duplicate_reference_note = CandidateReference.query.filter_by(candidate_id=candidate_id,
                                                                  person_name=reference_name,
                                                                  comments=reference_dict.get('comments')).first()
    if not duplicate_reference_note:
        candidate_reference = CandidateReference(**reference_dict)
        db.session.add(candidate_reference)
        db.session.flush()
        return candidate_reference.id
    else:
        raise InvalidUsage(error_message="Reference already exists for candidate",
                           error_code=custom_error.REFERENCE_EXISTS,
                           additional_error_info={'reference_id': duplicate_reference_note.id,
                                                  'candidate_id': candidate_id})


def update_reference(candidate_id, reference_id, reference_dict):
    """
    Function will validate and update Candidate Reference
    """
    candidate_reference_query = CandidateReference.query.filter_by(id=reference_id)
    candidate_reference_obj = candidate_reference_query.first()

    # Reference ID must be recognized
    if not candidate_reference_obj:
        raise InvalidUsage("Reference ID ({}) not recognized".format(reference_id))

    # CandidateReference must belong to specified candidate
    if candidate_reference_obj.candidate_id != candidate_id:
        raise ForbiddenError("Reference (id={}) does not belong to candidate (id={})".
                             format(reference_id, candidate_id))

    candidate_reference_query.update(reference_dict)
    return


def add_reference_email(reference_id, reference_email_dict):
    """
    Function will add reference's email info
    Function will check db to prevent adding duplicate records
    """
    if not ReferenceEmail.query.filter_by(reference_id=reference_id).first():
        reference_email_dict.update(reference_id=reference_id)
        db.session.add(ReferenceEmail(**reference_email_dict))
    return


def update_reference_email(reference_id, reference_email_dict):
    """
    Function will update reference-email's info
    """
    # Reference Email must already exist
    reference_email_query = ReferenceEmail.query.filter_by(reference_id=reference_id)
    if not reference_email_query.first():
        raise InvalidUsage("Unable to update. Reference email does not exist.", custom_error.REFERENCE_NOT_FOUND)

    reference_email_dict.update(reference_id=reference_id)
    reference_email_query.update(reference_email_dict)
    return


def add_reference_phone(reference_id, reference_phone_dict):
    """
    Function will add reference's phone info
    Function will check db to prevent adding duplicate records
    """
    if not ReferencePhone.query.filter_by(reference_id=reference_id).first():
        reference_phone_dict.update(reference_id=reference_id)
        db.session.add(ReferencePhone(**reference_phone_dict))
    return


def update_reference_phone(reference_id, reference_phone_dict):
    """
    Function will update Reference Phone
    """
    reference_phone_query = ReferencePhone.query.filter_by(reference_id=reference_id)
    if not reference_phone_query.first():
        raise InvalidUsage("Unable to update. Reference phone does not exist.")

    reference_phone_dict.update(reference_id=reference_id)
    reference_phone_query.update(reference_phone_dict)
    return


def add_reference_web_address(reference_id, reference_web_address_dict):
    """
    Function will add reference's web address info
    Function will check db to prevent adding duplicate records
    """
    if not ReferencePhone.query.filter_by(reference_id=reference_id).first():
        reference_web_address_dict.update(reference_id=reference_id)
        db.session.add(ReferenceWebAddress(**reference_web_address_dict))
    return


def update_reference_web_address(reference_id, reference_web_address_dict):
    """
    Function will update Reference Web Address
    """
    # ReferenceWebAddress must already exist
    reference_web_query = ReferenceWebAddress.query.filter_by(reference_id=reference_id)
    if not reference_web_query.first():
        raise InvalidUsage("Unable to update. Reference web address does not exist.")

    reference_web_address_dict.update(reference_id=reference_id)
    reference_web_query.update(reference_web_address_dict)
    return


def delete_reference(candidate_reference):
    """
    :type candidate_reference:  CandidateReference
    :rtype:  dict
    """
    db.session.delete(candidate_reference)
    db.session.commit()
    return {'id': candidate_reference.id}


def delete_all_references(candidate_references):
    """
    :type candidate_references:  list[CandidateReference]
    :rtype:  list[dict]
    """
    deleted_candidate_references = []
    for reference in candidate_references:
        deleted_candidate_references.append(delete_reference(reference))
    return deleted_candidate_references
