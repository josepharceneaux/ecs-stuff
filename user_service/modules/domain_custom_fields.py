"""
This file contains helpers functions for
  - retrieving custom fields from db
  - adding custom fields to db
"""
import datetime

from flask import request

# Models
from user_service.common.models.db import db
from user_service.common.models.misc import CustomField, CustomFieldCategory
from user_service.common.models.user import User

# Error handling
from user_service.common.error_handling import NotFoundError, ForbiddenError, InvalidUsage

from user_service.common.utils.handy_functions import normalize_value


def get_custom_field_if_validated(custom_field_id, user):
    """
    Function will return CustomField object if it's found and it belongs to user's domain
    :type custom_field_id:  int | long
    :type user: User
    :rtype: CustomField
    """
    # Custom field ID must be recognized
    custom_field = CustomField.get(custom_field_id)
    if not custom_field:
        raise NotFoundError("Custom field ID ({}) not recognized.".format(custom_field_id))

    # Custom field must belong to user's domain
    if request.user.role.name != 'TALENT_ADMIN' and custom_field.domain_id != user.domain_id:
        raise ForbiddenError("Not authorized")

    return custom_field


def create_custom_fields(custom_fields, domain_id):
    """
    Function will insert domain custom fields after passing validation
    :type custom_fields:  dict
    :type domain_id:  int | long
    :rtype: list[dict]
    """
    created_custom_fields = []
    for custom_field in custom_fields:

        cf_name = custom_field['name'].strip()
        if not cf_name:  # In case name is just a whitespace
            raise InvalidUsage("Custom field name is required for creating custom field(s).")

        cf_category_id = custom_field.get('category_id')

        # Custom field category ID must be recognized
        if cf_category_id:
            cf_category_obj = CustomFieldCategory.get(cf_category_id)
            if not cf_category_obj:
                raise NotFoundError("Custom field category ID ({}) not recognized.".format(cf_category_id))

        # Prevent duplicate entries for the same domain
        custom_field_obj = CustomField.query.filter_by(domain_id=domain_id,
                                                       name=cf_name).first()
        if custom_field_obj:
            raise InvalidUsage(error_message='Domain Custom Field already exists',
                               additional_error_info={'id': custom_field_obj.id})

        cf = CustomField(
            domain_id=domain_id,
            category_id=cf_category_id,
            name=cf_name,
            type="string",
            added_time=datetime.datetime.utcnow()
        )
        db.session.add(cf)
        db.session.flush()
        created_custom_fields.append(dict(id=cf.id))

    db.session.commit()
    return created_custom_fields
