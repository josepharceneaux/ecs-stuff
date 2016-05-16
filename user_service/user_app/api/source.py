"""
File contains endpoints for creating & retrieving domain source(s)
"""
# Standard libraries
import requests, json, datetime

# Flask specific
from flask import request
from flask_restful import Resource

# Validators
from user_service.common.utils.validators import get_json_data_if_validated

# Models
from user_service.common.models.db import db
from user_service.common.models.candidate import CandidateSource

# JSON Schemas
from user_service.modules.json_schema import source_schema

# Decorators
from user_service.common.utils.auth_utils import require_oauth

# Error handling
from user_service.common.error_handling import (ForbiddenError, InvalidUsage)


class DomainSourceResource(Resource):
    decorators = [require_oauth()]

    def post(self, **kwargs):
        """
        Function will create a source for domain
        Note: "description" is a required field
        Endpoint:  POST /v1/sources
        Example:
            >>> url = 'host/v1/sources'
            >>> headers = {'Authorization': 'Bearer {access_token}', 'content-type': 'application/json'}
            >>> data = {"source": {"description": "job fair", "notes": "recruiter initials: ahb"}}
            >>> requests.post(url=url, headers=headers, data=json.dumps(data))
        :return:  {'source': {'id': int}}
        """
        authed_user = request.user  # Authenticated user
        domain_id = authed_user.domain_id  # user's domain ID

        # Validate and obtain json data from request body
        body_dict = get_json_data_if_validated(request_body=request, json_schema=source_schema, format_checker=False)

        # Normalize description & notes
        source = body_dict['source']
        description, notes = source['description'].strip().lower(), (source.get('notes') or '').strip().lower()

        # In case description is just a whitespace
        if not description:
            raise InvalidUsage("Source description is a required field")

        # Prevent duplicate sources for the same domain
        source = CandidateSource.get_by(domain_id=domain_id, description=description)
        if source:
            raise InvalidUsage("Source (description: {}) already exists for domain: {}".format(description, domain_id),
                               additional_error_info=dict(source_id=source.id))

        new_source = CandidateSource(
            description=description, notes=notes, domain_id=domain_id, added_datetime=datetime.datetime.utcnow()
        )
        db.session.add(new_source)
        db.session.commit()
        return {'source': {'id': new_source.id}}, 201

    def get(self, **kwargs):
        """
        Function will return domain source(s)
        Endpoints:
             i. GET /v1/sources
            ii. GET /v1/sources/:id
        Example:
            >>> url = 'host/v1/sources'
            >>> headers = {'Authorization': 'Bearer {access_token}'}
            >>> requests.get(url=url, headers=headers)
        :returns:
            {'source': CandidateSource} if source_id is provided in url
            {'source': [CandidateSource, CandidateSource, ...]} if source_id is not provided in url
        """
        # Authenticated user & source ID
        authed_user, source_id = request.user, kwargs.get('id')
        domain_id = authed_user.domain_id  # User's domain ID

        # Return a single source If source ID is provided
        if source_id:
            source = CandidateSource.get(source_id)
            # Source ID must be recognized
            if not source_id:
                raise InvalidUsage("Source ID ({}) not recognized.".format(source_id))

            # Source must belong to user's domain
            if source.domain_id != authed_user.domain_id:
                raise ForbiddenError(
                    "Source (ID: {}) does not belong to user's domain (ID: )".format(source_id, domain_id))

            return {'source': {
                'id': source.id,
                'description': source.description,
                'notes': source.notes,
                'domain_id': source.domain_id,
                'added_datetime': str(source.added_datetime)
            }}
        # Get all of user's domain sources
        return {'sources': [
            {
                'id': source.id,
                'description': source.description,
                'notes': source.notes,
                'domain_id': source.domain_id,
                'added_datetime': str(source.added_datetime)
            } for source in CandidateSource.domain_sources(domain_id=domain_id)]}
