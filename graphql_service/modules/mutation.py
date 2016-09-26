import datetime
import graphene

from graphql_service.common.models.db import db
from graphql_service.common.models.user import Domain
from graphql_service.common.models.candidate import Candidate
from schema import CandidateType

from helpers import ValidateAndSave

from ..dynamodb.dynamo_actions import DynamoDB, set_empty_strings_to_null

# Utilites
from graphql_service.common.utils.datetime_utils import DatetimeUtils


class AddressInput(graphene.InputObjectType):
    address_line_1 = graphene.String()
    address_line_2 = graphene.String()
    city = graphene.String()
    state = graphene.String()
    zip_code = graphene.String()
    po_box = graphene.String()
    is_default = graphene.Boolean()
    coordinates = graphene.String()
    updated_time = graphene.String()
    iso3166_subdivision = graphene.String()
    iso3166_country = graphene.String()


class EmailInput(graphene.InputObjectType):
    address = graphene.String()
    label = graphene.String()
    is_default = graphene.Boolean()


class EducationDegreeInput(graphene.InputObjectType):
    degree_type = graphene.String()
    degree_title = graphene.String()
    start_year = graphene.Int()
    start_month = graphene.Int()
    end_year = graphene.Int()
    end_month = graphene.Int()
    gpa = graphene.Float()
    added_datetime = graphene.String()
    updated_datetime = graphene.String()
    concentration = graphene.String()
    comments = graphene.String()


class EducationInput(graphene.InputObjectType):
    school_name = graphene.String()
    school_type = graphene.String()
    city = graphene.String()
    state = graphene.String()
    iso3166_subdivision = graphene.String()
    is_current = graphene.Boolean()
    added_datetime = graphene.String()
    updated_datetime = graphene.String()

    # Nested data
    degrees = graphene.List(EducationDegreeInput)


class CreateCandidate(graphene.Mutation):
    ok = graphene.Boolean()
    id = graphene.Int()
    candidate = graphene.Field('CandidateType')

    class Input(object):
        """
        Class contains optional input fields for creating candidate
        """
        # Primary data
        first_name = graphene.String()
        middle_name = graphene.String()
        last_name = graphene.String()
        formatted_name = graphene.String()
        user_id = graphene.Int()
        filename = graphene.String()
        objective = graphene.String()
        summary = graphene.String()
        total_months_experience = graphene.Int()
        added_time = graphene.String()
        updated_datetime = graphene.String()
        candidate_status_id = graphene.Int()
        source_id = graphene.Int()
        culture_id = graphene.Int()

        # Secondary data
        emails = graphene.List(EmailInput)
        addresses = graphene.List(AddressInput)
        educations = graphene.List(EducationInput)

    @classmethod
    def mutate(cls, instance, args, info):
        candidate_data = dict(
            first_name=args.get('firstName'),
            middle_name=args.get('middleName'),
            last_name=args.get('lastName'),
            formatted_name=args.get('formattedName'),
            # user_id=request.user.id, # TODO: will work after user is authenticated
            filename=args.get('resumeUrl'),
            objective=args.get('objective'),
            summary=args.get('summary'),
            added_time=args.get('addedTime') or datetime.datetime.utcnow(),
            candidate_status_id=args.get('statusId'),
            source_id=args.get('sourceId'),
            culture_id=args.get('culutureId')
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

        # Educations
        educations = args.get('educations')
        if educations:
            ValidateAndSave.educations(educations)

        DynamoDB.add_candidate(set_empty_strings_to_null(ValidateAndSave.candidate_data))

        # Commit transaction
        db.session.commit()

        return CreateCandidate(candidate=CandidateType(**candidate_data),
                               ok=ok,
                               id=candidate_id)


class CandidateMutation(graphene.ObjectType):
    create_candidate = graphene.Field(CreateCandidate)
