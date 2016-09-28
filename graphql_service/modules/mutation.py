import datetime
import graphene

from graphql_service.common.models.db import db
from graphql_service.common.models.user import Domain
from graphql_service.common.models.candidate import Candidate
from schema import CandidateType

from helpers import ValidateAndSave, ValidatedCandidateData

from ..dynamodb.dynamo_actions import DynamoDB, set_empty_strings_to_null

# Utilities
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


class PhoneInput(graphene.InputObjectType):
    label = graphene.String()
    value = graphene.String()
    is_default = graphene.Boolean()


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
        addresses = graphene.List(AddressInput)
        educations = graphene.List(EducationInput)
        emails = graphene.List(EmailInput)
        phones = graphene.List(PhoneInput)

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
            added_time=args.get('added_datetime') or datetime.datetime.utcnow(),
            candidate_status_id=args.get('status_id'),
            source_id=args.get('source_id'),
            culture_id=args.get('culture_id')
        )

        # Insert candidate into MySQL database
        new_candidate = Candidate(**candidate_data)
        db.session.add(new_candidate)
        db.session.flush()

        candidate_id = new_candidate.id

        # We need candidate's MySQL-generated ID as a unique identifier for DynamoDB's primary key
        # DynamoDB does not accept datetime objects, hence it must be converted to string
        del candidate_data['added_time']
        candidate_data.update(
            id=candidate_id,
            added_datetime=DatetimeUtils.to_utc_str(datetime.datetime.utcnow())
        )

        addresses = args.get('addresses')
        educations = args.get('educations')
        emails = args.get('emails')
        phones = args.get('phones')

        # Save candidate's primary data
        # ValidateAndSave.candidate_data = candidate_data
        candidate_ = ValidatedCandidateData(
            primary_data=candidate_data,
            addresses_data=addresses,
            educations_data=educations,
            emails_data=emails,
            phones_data=phones
        )

        ok = True  # TODO: Dynamically set after adequate validations

        # Commit transaction
        db.session.commit()

        # DynamoDB.add_candidate(set_empty_strings_to_null(ValidateAndSave.candidate_data))
        DynamoDB.add_candidate(set_empty_strings_to_null(candidate_.candidate_data))

        return CreateCandidate(candidate=CandidateType(**candidate_data),
                               ok=ok,
                               id=candidate_id)


class CandidateMutation(graphene.ObjectType):
    create_candidate = graphene.Field(CreateCandidate)
