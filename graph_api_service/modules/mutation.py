import datetime
import graphene
from graphene import String, Boolean, List, Int

from graph_api_service.common.models.db import db
from graph_api_service.common.models.user import Domain
from graph_api_service.common.models.candidate import Candidate
from schema import CandidateType

from helpers import ValidateAndSave

from ..dynamodb.dynamo_actions import DynamoDB, set_empty_strings_to_null

# Utilites
from graph_api_service.common.utils.datetime_utils import DatetimeUtils


class AddressInput(graphene.InputObjectType):
    address_line_1 = String()
    address_line_2 = String()
    city = String()
    state = String()
    zip_code = String()
    po_box = String()
    is_default = graphene.Boolean()
    coordinates = String()
    updated_time = String()
    iso3166_subdivision = String()
    iso3166_country = String()


class EmailInput(graphene.InputObjectType):
    address = String()
    label = String()
    is_default = Boolean()


class CreateCandidate(graphene.Mutation):
    ok = graphene.Boolean()
    id = Int()
    candidate = graphene.Field('CandidateType')

    class Input(object):
        """
        Class contains optional input fields for creating candidate
        """
        # Primary data
        first_name = String()
        middle_name = String()
        last_name = String()
        formatted_name = String()
        user_id = Int()
        filename = String()
        objective = String()
        summary = String()
        total_months_experience = Int()
        added_time = String()
        updated_datetime = String()
        candidate_status_id = Int()
        source_id = Int()
        culture_id = Int()

        # Secondary data
        emails = List(EmailInput)
        addresses = List(AddressInput)
        # educations = List(EducationInput)

    @classmethod
    def mutate(cls, instance, args, info):
        candidate_data = dict(
            first_name=args.get('first_name'),
            middle_name=args.get('middle_name'),
            last_name=args.get('last_name'),
            formatted_name=args.get('formatted_name'),
            # user_id=request.user.id, # TODO: will work after user is authenticated
            filename=args.get('resume_url'),
            objective=args.get('objective'),
            summary=args.get('summary'),
            added_time=args.get('added_time') or datetime.datetime.utcnow(),
            candidate_status_id=args.get('status_id'),
            source_id=args.get('source_id'),
            culture_id=args.get('culuture_id')
        )

        # Insert candidate into MySQL database
        new_candidate = Candidate(**candidate_data)
        db.session.add(new_candidate)
        db.session.flush()

        candidate_id = new_candidate.id

        candidate_data.update(
            id=candidate_id,
            added_time=DatetimeUtils.to_utc_str(datetime.datetime.utcnow())
        )

        # Save candidate's primary data
        ValidateAndSave.candidate_data = candidate_data

        ok = True  # TODO: Dynamically set after adequate validations

        # Addresses
        addresses = args.get('addresses')
        if addresses:
            ValidateAndSave.addresses(addresses)

        # Emails
        emails = args.get('emails')
        if emails:
            ValidateAndSave.emails(emails)

        DynamoDB.add_candidate(set_empty_strings_to_null(ValidateAndSave.candidate_data))

        # Commit transaction
        db.session.commit()

        return CreateCandidate(candidate=CandidateType(**candidate_data),
                               ok=ok,
                               id=candidate_id)


class CandidateMutation(graphene.ObjectType):
    create_candidate = graphene.Field(CreateCandidate)
