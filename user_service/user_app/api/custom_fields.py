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

# Decorators
from user_service.common.utils.auth_utils import require_oauth

# Validators
from user_service.common.utils.validators import get_json_data_if_validated
from user_service.modules.json_schema import custom_fields_schema

# Error handling
from user_service.common.error_handling import InvalidUsage


class DomainCustomFieldsResource(Resource):
    decorators = [require_oauth()]

    def post(self):
        """
        Function will create custom field(s) for user's domain
        resource url:  /v1/custom_fields
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
            cf_name = custom_field['name'].strip()
            if not cf_name:  # In case name is just a whitespace
                raise InvalidUsage("Name is required for creating custom field.")

            # Prevent duplicate entries for the same domain
            custom_field_obj = CustomField.get_by_filters(domain_id=domain_id, name=cf_name)
            if not custom_field_obj:
                custom_field_obj = CustomField(domain_id=domain_id, name=cf_name, type="string",
                                               added_time=datetime.datetime.utcnow())
                db.session.add(custom_field_obj)
                db.session.flush()
                created_custom_field_ids.append(custom_field_obj.id)

        db.session.commit()
        return {"custom_fields": [{"id": cf_id} for cf_id in created_custom_field_ids]}, 201

    def get(self):
        """
        Function will return domain's custom field(s)
        resource url:  /v1/custom_fields
        :return: {"custom_fields": [{"id": int}, {"id": int}, ...]}
        :rtype: dict[list[dict]]
        Usage:
            >>> headers = {"Authorization": "Bearer {access_token}"}
            >>> requests.get(url="host/v1/custom_fields", headers=headers)
            <Response [200]>
        """
        return {"custom_fields": [
            {
                "id": custom_field.id,
                "domain_id": custom_field.domain_id,
                "name": custom_field.name,
                "added_datetime": str(custom_field.added_time)
            } for custom_field in CustomField.get_domain_custom_fields(request.user.domain_id)]}
