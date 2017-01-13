# Standard library
import requests
from flask import request
from flask_restful import Resource

from candidate_service.common.error_handling import ForbiddenError
from candidate_service.common.models.user import Permission
from candidate_service.common.utils.auth_utils import require_oauth, require_all_permissions
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error
from candidate_service.json_schema.notes import notes_schema
from candidate_service.modules.notes import add_notes, get_notes, delete_note, delete_notes
from candidate_service.modules.talent_cloud_search import upload_candidate_documents
from candidate_service.modules.validators import (
    does_candidate_belong_to_users_domain, get_candidate_if_exists, get_json_data_if_validated
)


class CandidateNotesResource(Resource):
    decorators = [require_oauth()]

    @require_all_permissions(Permission.PermissionNames.CAN_ADD_CANDIDATE_NOTES)
    def post(self, **kwargs):
        """
        Endpoint:  POST /v1/candidates/:candidate_id/notes
        Function will add candidate's note(s) to database
        """
        # Validate and retrieve json data
        body_dict = get_json_data_if_validated(request, notes_schema)

        # Get authenticated user & Candidate ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check if candidate exists & is not web-hidden
        get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError('Not authorized', custom_error.CANDIDATE_FORBIDDEN)

        note_ids = add_notes(candidate_id=candidate_id, user_id=authed_user.id, data=body_dict['notes'])

        # Update cloud search
        upload_candidate_documents.delay([candidate_id])

        return {'candidate_notes': [{'id': note_id} for note_id in note_ids]}, requests.codes.CREATED

    @require_all_permissions(Permission.PermissionNames.CAN_GET_CANDIDATE_NOTES)
    def get(self, **kwargs):
        """
        Function will return all of candidate's notes if note ID is not provided,
        otherwise it will return specified candidate note
        Endpoints:
             i. GET /v1/candidates/:candidate_id/notes
            ii. GET /v1/candidates/:candidate_id/notes/:id
        """
        # Get authenticated user & candidate ID
        authed_user, candidate_id, note_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Check if candidate exists & is web-hidden
        candidate = get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError('Not authorized', custom_error.CANDIDATE_FORBIDDEN)

        return get_notes(candidate, note_id)

    @require_all_permissions(Permission.PermissionNames.CAN_DELETE_CANDIDATE_NOTES)
    def delete(self, **kwargs):
        """
        Function will delete all of candidate's notes if note ID is not provided,
        otherwise it will delete specified candidate note
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/notes
            ii. DELETE /v1/candidates/:candidate_id/notes/:id
        """
        # Get authenticated user & candidate ID
        authed_user, candidate_id, note_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Check if candidate exists & is not web-hidden
        candidate = get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError('Not authorized', custom_error.CANDIDATE_FORBIDDEN)

        # Delete candidate's note if note ID is provided, otherwise delete all of candidate's notes
        if note_id:

            # Delete note from DB & update cloud search
            delete_note(candidate_id, note_id)
            upload_candidate_documents.delay([candidate_id])

            return {'candidate_note': {'id': note_id}}
        else:
            # Delete notes from DB & update cloud search
            deleted_notes = delete_notes(candidate)
            upload_candidate_documents.delay([candidate_id])

            return {'candidate_notes': deleted_notes}
