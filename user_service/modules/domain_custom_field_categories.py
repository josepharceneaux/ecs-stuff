"""
This file contains helpers functions for
  - adding custom field categories to db
  - retrieving custom field categories from db, and
  - updating custom field categories
"""

# Models
from sqlalchemy.exc import SQLAlchemyError
from user_service.common.models.db import db
from user_service.common.models.misc import CustomField, CustomFieldCategory, CustomFieldSubCategory

# Error handling
from user_service.common.error_handling import NotFoundError, ForbiddenError, InvalidUsage
from user_service.user_app import logger


# TODO: move to app_common
def commit_transaction():
    """
    Commit current db transaction and rollback in case of an error
    """
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception('database transaction failed. Error: {}'.format(e.message))


def add_or_update_custom_fields(custom_fields_data, domain_id, is_creating=False):
    """

    :param custom_fields_data:
    :param domain_id:
    :param is_creating:
    :return:
    """
    custom_field_ids = []
    if is_creating:
        for custom_field in custom_fields_data:  # type: dict

            cf_name = custom_field['name'].strip()
            if not cf_name:  # In case it's just a whitespace
                raise InvalidUsage("Custom field name is required.")  # TODO: custom error codes

            # Prevent duplicate entries into the database
            cf_object = CustomField.query.filter_by(domain_id=domain_id, name=cf_name).first()  # type: CustomField
            if cf_object:
                raise InvalidUsage(error_message="Custom field already exists.",
                                   additional_error_info={"id": cf_object.id, "domain_id": domain_id})

            # Add domain custom field
            cf = CustomField(domain_id=domain_id, name=cf_name, type='string')
            db.session.add(cf)
            db.session.flush()
            cf_id = cf.id

            # Add custom field categories and subcategories if provided
            _add_or_update_categories(custom_field_id=cf_id,
                                      custom_field_categories=(custom_field.get('categories') or []),
                                      is_creating=is_creating)

            custom_field_ids.append(cf_id)
    else:  # updating existing custom field(s)
        for custom_field in custom_fields_data:  # type: dict
            cf_id = custom_field['id']
            cf_object = CustomField.get(cf_id)  # type: CustomField
            if not cf_object:
                raise InvalidUsage(error_message='Custom field ID not recognized')  # todo: custom error codes

            if cf_object.domain_id != domain_id:
                raise ForbiddenError(error_message='Custom field update forbidden')  # todo: custom error codes

            # Add custom field categories & subcategories
            _add_or_update_categories(custom_field_id=cf_id,
                                      custom_field_categories=(custom_field.get('categories') or []),
                                      is_creating=is_creating)
            custom_field_ids.append(cf_id)

    commit_transaction()
    return custom_field_ids


def _add_or_update_categories(custom_field_id, custom_field_categories, is_creating):
    """
    :type custom_field_id: int | long
    :param custom_field_categories:
    :return:
    """
    for cf_category in custom_field_categories:  # type: dict
        cf_category_name = cf_category['name'].strip()
        if not cf_category_name:
            raise InvalidUsage("Custom-field-category name is required.")  # TODO: custom error codes

        # Updating existing custom field
        if not is_creating:
            # Prevent duplicate category entry for custom field during update
            category = CustomFieldCategory.query.filter_by(custom_field_id=custom_field_id,
                                                           name=cf_category_name).first()
            if category:
                cf_cat_id = category.id
            else:
                cf_cat_id = _add_custom_field_category(custom_field_id, cf_category_name)

            cf_subcategories = cf_category.get('subcategories') or []
            _add_custom_field_subcategories(cf_subcategories, cf_cat_id)
        else:
            # Add custom field category
            cf_cat_id = _add_custom_field_category(custom_field_id, cf_category_name)

            # Add subcategories if provided
            _add_custom_field_subcategories((cf_category.get('subcategories') or []), cf_cat_id)


def _add_custom_field_category(cf_id, cf_category_name):
    """
    Function will add custom field categories to database
    """
    cf_cat = CustomFieldCategory(custom_field_id=cf_id, name=cf_category_name)
    db.session.add(cf_cat)
    db.session.flush()
    return cf_cat.id


def _add_custom_field_subcategories(cf_subcategories, category_id=None):
    """
    Function will add custom field subcategories to database
    """
    for cf_subcategory in cf_subcategories:  # type: dict
        cf_subcategory_name = cf_subcategory['name'].strip()

        # Prevent possible whitespace
        if not cf_subcategory_name:
            raise InvalidUsage("Custom-field-subcategory name is required.")  # TODO: custom error codes

        # Prevent duplicate subcategory for custom field category during update
        if category_id and not CustomFieldSubCategory.query.filter_by(
                custom_field_category_id=category_id, name=cf_subcategory_name
        ).first():
            db.session.add(CustomFieldSubCategory(custom_field_category_id=category_id, name=cf_subcategory_name))


def retrieve_domain_custom_fields(domain_id, custom_field_id=None):
    """
    Function will return domain's custom field category if custom field category ID is provided,
    otherwise it will return all of domain's custom field categories
    :type domain_id:  int
    :type custom_field_id:  int | None
    :rtype:  dict[dict] | dict[list]
    """
    if custom_field_id:

        custom_field = CustomField.get(custom_field_id)  # type: CustomField

        # Custom field category ID must be recognized
        if not custom_field:
            raise NotFoundError(error_message="Custom field ID is not recognized")  # TODO: custom error codes

        # Custom field category must belong to user's domain
        if custom_field.domain_id != domain_id:
            raise ForbiddenError("Unauthorized custom field")  # TODO: custom error codes

        return {
            'custom_field': {
                'id': custom_field.id,
                'domain_id': custom_field.domain_id,
                'name': custom_field.name,
                'categories': [
                    {
                        'id': category.id,
                        'name': category.name,
                        'subcategories': _get_cf_subcategories(category)
                    } for category in custom_field.categories]
            }
        }
    else:  # return all of user's domain custom field categories
        # custom_fields = CustomField.get_domain_custom_fields(domain_id)  # type: [CustomField]
        return {
            'custom_fields': [
                {
                    'id': custom_field.id,
                    'name': custom_field.name,
                    'categories': [
                        {
                            'id': category.id,
                            'name': category.name,
                            'subcategories': _get_cf_subcategories(category)
                        } for category in custom_field.categories]
                } for custom_field in CustomField.get_domain_custom_fields(domain_id)]
        }


def _get_cf_subcategories(cf_category):
    """
    Function will retrieve custom field subcategories from database
    :type cf_category: CustomFieldCategory
    :rtype: list
    """
    return [{
                'id': sub_cat.id,
                'name': sub_cat.name
            } for sub_cat in cf_category.subcategories]
