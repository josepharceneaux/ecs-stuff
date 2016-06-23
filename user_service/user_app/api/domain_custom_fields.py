"""
File contains endpoint(s) for creating & retrieving domain custom fields
"""
# Standard libraries
import requests, json, datetime

# Flask specific
from flask import request
from flask_restful import Resource

# Models
from user_service.common.models.db import db
from user_service.common.models.misc import CustomField
from user_service.common.models.user import Permission

# Decorators
from user_service.common.utils.auth_utils import require_oauth, require_all_permissions

# Validators
from user_service.common.utils.validators import get_json_data_if_validated
from user_service.modules.json_schema import custom_fields_schema, custom_field_schema

# Error handling
from user_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError

# Helpers
from user_service.common.utils.handy_functions import normalize_value
from user_service.modules.domain_custom_fields import get_custom_field_if_validated


class DomainCustomFieldsResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def post(self):
        """
        Function will create custom field(s) for user's domain
        resource url:  POST /v1/custom_fields
        :return: {"custom_fields": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> data = {"custom_fields": [{"name": "job status"}]}
            >>> headers = {"Authorization": "Bearer {access_token}", "content-type": "application/json"}
            >>> requests.post(url="host/v1/custom_fields", data=json.dumps(data), headers=headers)
            <Response [201]>
        """
        # Authenticated user
        authed_user = request.user
        domain_id = authed_user.domain_id

        # Validate and obtain json data from request body
        body_dict = get_json_data_if_validated(request, custom_fields_schema, False)

        created_custom_field_ids = []
        for custom_field in body_dict['custom_fields']:

            # Normalize custom field name
            cf_name = normalize_value(custom_field['name'])
            if not cf_name:  # In case name is just a whitespace
                raise InvalidUsage("Name is required for creating custom field.")

            # Prevent duplicate entries for the same domain
            custom_field_obj = CustomField.query.filter_by(domain_id=domain_id, name=cf_name).first()
            if custom_field_obj:
                raise InvalidUsage(error_message='Domain Custom Field already exists',
                                   additional_error_info={'id': custom_field_obj.id})

            cf = CustomField(domain_id=domain_id, name=cf_name, type="string",
                             added_time=datetime.datetime.utcnow())
            db.session.add(cf)
            db.session.flush()
            created_custom_field_ids.append(cf.id)

        db.session.commit()
        return {"custom_fields": [{"id": cf_id} for cf_id in created_custom_field_ids]}, 201

    @require_all_permissions(Permission.PermissionNames.CAN_GET_DOMAINS)
    def get(self, **kwargs):
        """
        Function will return domain's custom field(s)
        resource url:
             i. GET /v1/custom_fields
            ii. GET /v1/custom_fields/:id
        :return: {"custom_fields": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.get(url="host/v1/custom_fields", headers=headers)
            <Response [200]>
        """
        custom_field_id = kwargs.get('id')

        # Return specified custom field data
        if custom_field_id:
            # Custom field ID must be recognized & belong to user's domain
            custom_field = get_custom_field_if_validated(custom_field_id, request.user)

            return {'custom_field': {
                'id': custom_field.id,
                'domain_id': custom_field.domain_id,
                'name': custom_field.name,
                'added_datetime': str(custom_field.added_time)
            }}

        # Return all of domain's custom fields
        return {"custom_fields": [
            {
                "id": custom_field.id,
                "domain_id": custom_field.domain_id,
                "name": custom_field.name,
                "added_datetime": str(custom_field.added_time)
            } for custom_field in CustomField.get_domain_custom_fields(request.user.domain_id)]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def put(self, **kwargs):
        """
        Function will update domain's custom field(s)
        resource url:
             i. PUT /v1/custom_fields
            ii. PUT /v1/custom_fields/:id
        :return: {"custom_fields": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> data = {"custom_fields": [{"id": 4, "name": "job status"}]}
            >>> requests.put(url="host/v1/custom_fields", headers=headers, data=json.dumps(data))
            <Response [200]>
        """
        custom_field_id = kwargs.get('id')

        # Validate and obtain json data from request body
        schema = custom_field_schema if custom_field_id else custom_fields_schema
        body_dict = get_json_data_if_validated(request, schema, False)

        # Update specified custom field
        if custom_field_id:

            # Custom field ID must be recognized & belong to user's domain
            get_custom_field_if_validated(custom_field_id, request.user)

            # Normalize custom field name
            custom_field_name = normalize_value(body_dict['custom_field']['name'])
            if not custom_field_name:  # In case name is just a whitespace
                raise InvalidUsage("Name is required for creating custom field.")

            custom_field_query = CustomField.query.filter_by(id=custom_field_id)
            custom_field_query.update(dict(name=custom_field_name))
            db.session.commit()

            return {'custom_field': {'id': custom_field_id}}

        updated_custom_field_ids = []
        for custom_field in body_dict['custom_fields']:

            # Custom field ID must be provided
            custom_field_id = custom_field.get('id')
            if not custom_field_id:
                raise InvalidUsage("Custom field ID is required for updating.")

            # Normalize custom field name
            custom_field_name = normalize_value(custom_field['name'])

            custom_field_query = CustomField.query.filter_by(id=custom_field_id)

            # Custom field ID must be recognized
            cf_object = custom_field_query.first()
            if not cf_object:
                raise NotFoundError('Custom field ID ({}) not recognized.'.format(custom_field_id))

            # Custom field must belong to user's domain
            if cf_object.domain_id != request.user.domain_id:
                raise ForbiddenError('Not authorized')

            custom_field_query.update(dict(name=custom_field_name))
            updated_custom_field_ids.append(custom_field_id)

        db.session.commit()
        return {'custom_fields': [{'id': custom_field_id} for custom_field_id in updated_custom_field_ids]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_DOMAINS)
    def delete(self, **kwargs):
        """
        Function will delete domain's custom field(s)
        resource url:
            i. DELETE /v1/custom_fields/:id
        :return: {"custom_field": {"id": int}}
        :rtype: dict[dict]
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.delete(url="host/v1/custom_fields/4", headers=headers)
            <Response [200]>
        """
        custom_field_id = kwargs.get('id')

        # Delete specified custom field
        if custom_field_id:

            # Custom field ID must be recognized
            custom_field = CustomField.get(custom_field_id)
            if not custom_field:
                raise NotFoundError("Custom field ID ({}) not recognized.".format(custom_field_id))

            # Custom field must belong to user's domain
            if custom_field.domain_id != request.user.domain_id:
                raise ForbiddenError("Not authorized")

            db.session.delete(custom_field)
            db.session.commit()

            return {'custom_field': {'id': custom_field_id}}
