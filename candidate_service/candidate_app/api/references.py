# Flask specific
from flask import request
from flask_restful import Resource

# Validators
from candidate_service.modules.validators import (
    does_candidate_belong_to_users_domain, get_candidate_if_exists, get_json_data_if_validated
)
from candidate_service.json_schema.references import references_schema

# Decorators
from candidate_service.common.utils.auth_utils import require_oauth, require_all_roles

# Error handling
from candidate_service.common.error_handling import ForbiddenError, NotFoundError
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error

# Models
from candidate_service.common.models.candidate import CandidateReference
from candidate_service.common.models.user import DomainRole
from candidate_service.modules.references import (
    get_references, get_reference_emails, get_reference_phones, get_reference_web_addresses,
    create_or_update_references, delete_reference, delete_all_references
)


class CandidateReferencesResource(Resource):
    decorators = [require_oauth()]

    @require_all_roles(DomainRole.Roles.CAN_EDIT_CANDIDATES)
    def post(self, **kwargs):
        """
        Endpoint:   POST /v1/candidates/:candidate_id/references
        :return     {'candidate_references': [{'id': int}, {'id': int}, ...]}
                    status code: 201
        """
        # Get json data if exists and validate its schema
        body_dict = get_json_data_if_validated(request, references_schema)

        # Get authenticated user & candidate ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']

        # Check if candidate exists & is not web-hidden
        get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError("Not authorized", custom_error.CANDIDATE_FORBIDDEN)

        created_reference_ids = create_or_update_references(candidate_id=candidate_id,
                                                            references=body_dict['candidate_references'],
                                                            is_creating=True)
        return {'candidate_references': [{'id': reference_id} for reference_id in created_reference_ids]}, 201

    @require_all_roles(DomainRole.Roles.CAN_GET_CANDIDATES)
    def get(self, **kwargs):
        """
        Endpoints:
             i. GET /v1/candidates/:candidate_id/references
            ii. GET /v1/candidates/:candidate_id/references/:id
        """
        # Get authenticated user, candidate ID, and reference ID
        authed_user, candidate_id, reference_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Check if candidate exists & is web-hidden
        candidate = get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError("Not authorized", custom_error.CANDIDATE_FORBIDDEN)

        if reference_id:
            # Reference ID must be recognized
            reference = CandidateReference.get(reference_id)
            if not reference:
                raise NotFoundError("Reference ID ({}) not recognized.".format(reference_id),
                                    custom_error.REFERENCE_NOT_FOUND)

            # Reference must belong to candidate
            if reference.candidate_id != candidate_id:
                raise ForbiddenError("Reference (id={}) does not belong to candidate (id={})".
                                     format(reference_id, candidate_id), custom_error.REFERENCE_FORBIDDEN)

            return dict(candidate_reference=dict(id=reference_id,
                                                 name=reference.person_name,
                                                 position_title=reference.position_title,
                                                 comments=reference.comments,
                                                 reference_email=get_reference_emails(reference_id),
                                                 reference_phone=get_reference_phones(reference_id),
                                                 reference_web_address=get_reference_web_addresses(reference_id)))

        return {'candidate_references': get_references(candidate)}

    @require_all_roles(DomainRole.Roles.CAN_EDIT_CANDIDATES)
    def patch(self, **kwargs):
        """
        Function will update candidate's references' information
        Candidate Reference ID must be provided for a successful response
        Endpoints:
             i. PATCH /v1/candidates/:candidate_id/references
            ii. PATCH /v1/candidates/:candidate_id/references/:id
        """
        # Get json data if provided and passed schema validation
        body_dict = get_json_data_if_validated(request, references_schema)

        # Authenticated user, candidate ID, and reference ID
        authed_user, candidate_id = request.user, kwargs['candidate_id']
        reference_id_from_url = kwargs.get('id')

        # Check if candidate exists & is web-hidden
        get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError("Not authorized", custom_error.CANDIDATE_FORBIDDEN)

        updated_reference_ids = create_or_update_references(candidate_id=candidate_id,
                                                            references=body_dict['candidate_references'],
                                                            is_updating=True,
                                                            reference_id_from_url=reference_id_from_url)
        return {'updated_candidate_references': [{'id': reference_id} for reference_id in updated_reference_ids]}

    @require_all_roles(DomainRole.Roles.CAN_EDIT_CANDIDATES)
    def delete(self, **kwargs):
        """
        Endpoints:
             i. DELETE /v1/candidates/:candidate_id/references
            ii. DELETE /v1/candidates/:candidate_id/references/:id
        :return
            {'candidate_reference': {'id': int}}                        If a single reference was deleted, OR
            {'candidate_references': [{'id': int}, {'id': int}, ...]}   If all references were deleted
            status code: 200
        """
        # Get authenticated user, candidate ID, and reference ID
        authed_user, candidate_id, reference_id = request.user, kwargs['candidate_id'], kwargs.get('id')

        # Check if candidate exists & is web-hidden
        candidate = get_candidate_if_exists(candidate_id)

        # Candidate must belong to user's domain
        if not does_candidate_belong_to_users_domain(authed_user, candidate_id):
            raise ForbiddenError("Not authorized", custom_error.CANDIDATE_FORBIDDEN)

        if reference_id:  # Delete specified reference
            candidate_reference = CandidateReference.get_by_id(reference_id)
            if not candidate_reference:  # Reference must be recognized
                raise NotFoundError("Candidate reference ({}) not found.".format(reference_id),
                                    custom_error.REFERENCE_NOT_FOUND)

            if candidate_reference.candidate_id != candidate_id:  # reference must belong to candidate
                raise ForbiddenError("Not authorized", custom_error.REFERENCE_FORBIDDEN)

            # Delete candidate reference and return its ID
            return {'candidate_reference': delete_reference(candidate_reference)}

        else:  # Delete all of candidate's references
            return {'candidate_references': delete_all_references(candidate.references)}
