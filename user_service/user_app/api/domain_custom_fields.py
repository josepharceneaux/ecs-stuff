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
from user_service.common.models.user import DomainRole

# Decorators
from user_service.common.utils.auth_utils import require_oauth, require_all_roles

# Validators
from user_service.common.utils.validators import get_json_data_if_validated
from user_service.modules.json_schema import custom_fields_schema

# Error handling
from user_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError


class DomainCustomFieldsResource(Resource):
    decorators = [require_oauth()]

    @require_all_roles(DomainRole.Roles.CAN_EDIT_DOMAINS)
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
            cf_name = custom_field['name'].strip().lower()
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

    @require_all_roles(DomainRole.Roles.CAN_GET_DOMAINS)
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

            # Custom field ID must be recognized
            custom_field = CustomField.get(custom_field_id)
            if not custom_field:
                raise NotFoundError("Custom field id ({}) not recognized.".format(custom_field_id))

            # Custom field must belong to user's domain
            if custom_field.domain_id != request.user.domain_id:
                raise ForbiddenError("Not authorized")

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

    @require_all_roles(DomainRole.Roles.CAN_EDIT_DOMAINS)
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
                raise NotFoundError("Custom field id ({}) not recognized.".format(custom_field_id))

            # Custom field must belong to user's domain
            if custom_field.domain_id != request.user.domain_id:
                raise ForbiddenError("Not authorized")

            db.session.delete(custom_field)
            db.session.commit()

            return {'custom_field': {'id': custom_field_id}}
