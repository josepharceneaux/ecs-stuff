# Standard library
import requests, json, datetime
# Flask specific
from flask import request
from flask_restful import Resource
# Models
from candidate_service.common.models.db import db
from candidate_service.common.models.candidate import CandidateCustomField
from candidate_service.common.models.user import Permission
from candidate_service.common.models.misc import CustomField
# Validators
from candidate_service.common.utils.auth_utils import require_oauth, require_all_permissions
from candidate_service.modules.validators import (
    get_candidate_if_validated, does_candidate_cf_exist, is_custom_field_authorized, get_json_data_if_validated
)
from candidate_service.json_schema.candidate_custom_fields import ccf_schema
# Error handling
from candidate_service.common.error_handling import InvalidUsage, NotFoundError, ForbiddenError
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error
# Cloud search
from candidate_service.modules.talent_cloud_search import upload_candidate_documents


class CandidateCustomFieldResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def post(self, **kwargs):
        """
        Endpoints:  POST /v1/candidates/:candidate_id/custom_fields
        Usage:
            >>> headers = {"Authorization": "Bearer access_token", "content-type": "application/json"}
            >>> data = {"candidate_custom_fields": [{"custom_field_id": 547, "value": "scripted"}]}
            >>> requests.post(url="hots/v1/candidates/4/custom_fields", headers=headers, data=json.dumps(data))
            <Response [201]>
        :return  {'candidate_custom_fields': [{'id': int}, {'id': int}, ...]}
        """
        # Validate data
        body_dict = get_json_data_if_validated(request, ccf_schema)

        # Get authenticated user and candidate ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Candidate must exists and must belong to user's domain
        candidate = get_candidate_if_validated(authed_user, candidate_id)

        created_ccf_ids = []  # aggregate created CandidateCustomField IDs
        candidate_custom_fields = body_dict['candidate_custom_fields']

        for candidate_custom_field in candidate_custom_fields:

            # Custom field value(s) must not be empty
            values = filter(None, [value.strip() for value in (candidate_custom_field.get('values') or []) if value]) \
                     or [candidate_custom_field['value'].strip()]
            if not values:
                raise InvalidUsage("Custom field value must be provided.", custom_error.INVALID_USAGE)

            # Custom Field must be recognized
            custom_field_id = candidate_custom_field['custom_field_id']
            custom_field = CustomField.get_by_id(custom_field_id)
            if not custom_field:
                raise NotFoundError("Custom field ID ({}) not recognized".format(custom_field_id),
                                    custom_error.CUSTOM_FIELD_NOT_FOUND)

            # Custom Field must belong to user's domain
            if custom_field.domain_id != candidate.user.domain_id:
                raise ForbiddenError("Custom field ID ({}) does not belong to user ({})".format(
                    custom_field_id, authed_user.id), custom_error.CUSTOM_FIELD_FORBIDDEN)

            custom_field_dict = dict(
                values=values,
                custom_field_id=custom_field_id
            )

            for value in custom_field_dict.get('values'):

                custom_field_id = candidate_custom_field.get('custom_field_id')

                # Prevent duplicate insertions
                if not does_candidate_cf_exist(candidate, custom_field_id, value):

                    added_time = datetime.datetime.utcnow()

                    candidate_custom_field = CandidateCustomField(
                        candidate_id=candidate_id,
                        custom_field_id=custom_field_id,
                        value=value,
                        added_time=added_time
                    )
                    db.session.add(candidate_custom_field)

                    db.session.commit()
                    created_ccf_ids.append(candidate_custom_field.id)

        upload_candidate_documents([candidate_id])
        return {'candidate_custom_fields': [{'id': custom_field_id} for custom_field_id in created_ccf_ids]}, 201

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoints:
             i. GET /v1/candidates/:candidate_id/custom_fields
            ii. GET /v1/candidates/:candidate_id/custom_fields/:id
        Depending on the endpoint requested, function will return all of Candidate's
        custom fields or just a single one.
        """
        # Get authenticated user, candidate_id, and can_cf_id
        authed_user, candidate_id, can_cf_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Candidate must exists and must belong to user's domain
        get_candidate_if_validated(authed_user, candidate_id)

        if can_cf_id:  # Retrieve specified custom field
            candidate_custom_field = CandidateCustomField.get_by_id(can_cf_id)
            if not candidate_custom_field:
                raise NotFoundError('Candidate custom field not found: {}'.format(can_cf_id),
                                    custom_error.CUSTOM_FIELD_NOT_FOUND)

            # Custom field must belong to user's domain
            custom_field_id = candidate_custom_field.custom_field_id
            if not is_custom_field_authorized(authed_user.domain_id, [custom_field_id]):
                raise ForbiddenError('Not authorized', custom_error.CUSTOM_FIELD_FORBIDDEN)

            # Custom Field must belong to candidate
            if candidate_custom_field.candidate_id != candidate_id:
                raise ForbiddenError("Candidate custom field ({}) does not belong to candidate ({})".format(
                    can_cf_id, candidate_id), custom_error.CUSTOM_FIELD_FORBIDDEN)

            return {
                'candidate_custom_field': {
                    'id': can_cf_id,
                    'custom_field_id': custom_field_id,
                    'value': candidate_custom_field.value,
                    'created_at_datetime': candidate_custom_field.added_time.isoformat()
                }
            }

        else:
            # Custom fields must belong user's domain
            return {'candidate_custom_fields': [
                {
                    'id': ccf.id,
                    'custom_field_id': ccf.custom_field_id,
                    'value': ccf.value,
                    'created_at_datetime': ccf.added_time.isoformat()
                } for ccf in CandidateCustomField.get_candidate_custom_fields(candidate_id)]}

    @require_all_permissions(Permission.PermissionNames.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/custom_fields
            ii. DELETE /v1/candidates/:candidate_id/custom_fields/:id
        Depending on the endpoint requested, function will delete all of Candidate's
        custom fields or just a single one.
        """
        # Get authenticated user, candidate_id, and can_cf_id (CandidateCustomField.id)
        authed_user, candidate_id, can_cf_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Candidate must exists and must belong to user's domain
        get_candidate_if_validated(authed_user, candidate_id)

        if can_cf_id:  # Delete specified custom field
            candidate_custom_field = CandidateCustomField.get_by_id(can_cf_id)
            if not candidate_custom_field:
                raise NotFoundError('Candidate custom field not found: {}'.format(can_cf_id),
                                    custom_error.CUSTOM_FIELD_NOT_FOUND)

            # Custom fields must belong to user's domain
            custom_field_id = candidate_custom_field.custom_field_id
            if not is_custom_field_authorized(authed_user.domain_id, [custom_field_id]):
                raise ForbiddenError('Not authorized', custom_error.CUSTOM_FIELD_FORBIDDEN)

            # Custom Field must belong to candidate
            if candidate_custom_field.candidate_id != candidate_id:
                raise ForbiddenError("Candidate custom field ({}) does not belong to candidate ({})".format(
                    can_cf_id, candidate_id), custom_error.CUSTOM_FIELD_FORBIDDEN)

            db.session.delete(candidate_custom_field)

        else:  # Delete all of Candidate's custom fields
            for ccf in CandidateCustomField.get_candidate_custom_fields(candidate_id):
                db.session.delete(ccf)

        db.session.commit()

        # Update cloud search
        upload_candidate_documents([candidate_id])
        return '', 204
