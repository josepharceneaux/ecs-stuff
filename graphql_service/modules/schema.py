import graphene

# Flask specific
from flask import request

# Error handling
from graphql_service.common.error_handling import InternalServerError


class CandidateAddressType(graphene.ObjectType):
    name = 'CandidateAddress'

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

    def resolve_address_line_1(self, args, info):
        return self.get('address_line_1')

    def resolve_address_line_2(self, args, info):
        return self.get('address_line_2')

    def resolve_city(self, args, info):
        return self.get('city')

    def resolve_state(self, args, info):
        return self.get('state')

    def resolve_zip_code(self, args, info):
        return self.get('zip_code')

    def resolve_po_box(self, args, info):
        return self.get('po_box')

    def resolve_is_default(self, args, info):
        return self.get('is_default')

    def resolve_coordinates(self, args, info):
        return self.get('coordinates')

    def resolve_updated_time(self, args, info):
        return self.get('updated_time')

    def resolve_iso3166_subdivision(self, args, info):
        return self.get('iso3166_subdivision')

    def resolve_iso3166_country(self, args, info):
        return self.get('iso3166_country')


class CandidateEmailType(graphene.ObjectType):
    name = 'CandidateEmail'

    address = graphene.String()
    label = graphene.String()
    is_default = graphene.Boolean()

    def resolve_label(self, args, info):
        return self.get('label')

    def resolve_address(self, args, info):
        return self.get('address')

    def resolve_is_default(self, args, info):
        return self.get('is_default')


class EducationDegreeType(graphene.ObjectType):
    degree_type = graphene.String()
    degree_title = graphene.String()
    start_year = graphene.Int()
    start_month = graphene.Int()
    end_year = graphene.Int()
    end_month = graphene.Int()
    gpa = graphene.Float()
    added_datetime = graphene.String()
    updated_datetime = graphene.String()
    major = graphene.String()
    comments = graphene.String()

    def resolve_degree_type(self, args, info):
        return self.get('degree_type')

    def resolve_degree_title(self, args, info):
        return self.get('degree_title')

    def resolve_start_year(self, args, info):
        return self.get('start_year')

    def resolve_start_month(self, args, info):
        return self.get('start_month')

    def resolve_end_year(self, args, info):
        return self.get('end_year')

    def resolve_end_month(self, args, info):
        return self.get('end_month')

    def resolve_gpa(self, args, info):
        return self.get('gpa')

    def resolve_added_datetime(self, args, info):
        return self.get('added_datetime')

    def resolve_updated_datetime(self, args, info):
        return self.get('updated_datetime')

    def resolve_major(self, args, info):
        return self.get('major')

    def resolve_comments(self, args, info):
        return self.get('comments')


class EducationType(graphene.ObjectType):
    school_name = graphene.String()
    school_type = graphene.String()
    city = graphene.String()
    state = graphene.String()
    iso3166_subdivision = graphene.String()
    is_current = graphene.Boolean()
    added_datetime = graphene.String()
    updated_datetime = graphene.String()

    # Nested data
    degrees = graphene.List(EducationDegreeType)

    def resolve_school_name(self, args, info):
        return self.get('school_name')

    def resolve_school_type(self, args, info):
        return self.get('school_type')

    def resolve_city(self, args, info):
        return self.get('city')

    def resolve_iso3166_subdivision(self, args, info):
        return self.get('iso3166_subdivision')

    def resolve_is_current(self, args, info):
        return self.get('is_current')

    def resolve_added_datetime(self, args, info):
        return self.get('added_datetime')

    def resolve_updated_datetime(self, args, info):
        return self.get('updated_datetime')

    def resolve_degrees(self, args, info):
        return self.degrees


class PhoneType(graphene.ObjectType):
    value = graphene.String()
    label = graphene.String()
    is_default = graphene.Boolean()

    def resolve_value(self, args, info):
        return self.get('value')

    def resolve_label(self, args, info):
        return self.get('label')

    def resolve_is_default(self, args, info):
        return self.get('is_default')


class CandidateType(graphene.ObjectType):
    """
    Note: Class variables must be identical to Candidate's class variables otherwise it
          will require a resolver
    """
    name = 'Candidate'

    # ***** Primary attributes *****
    id = graphene.Int()
    first_name = graphene.String()
    middle_name = graphene.String()
    last_name = graphene.String()
    formatted_name = graphene.String()
    user_id = graphene.Int()
    filename = graphene.String()
    objective = graphene.String()
    summary = graphene.String()
    total_months_experience = graphene.Int()
    added_datetime = graphene.String()
    updated_datetime = graphene.String()
    candidate_status_id = graphene.Int()
    source_id = graphene.Int()
    culture_id = graphene.Int()

    def resolve_first_name(self, args, info):
        return self.get('first_name')

    def resolve_middle_name(self, args, info):
        return self.get('middle_name')

    def resolve_last_name(self, args, info):
        return self.get('last_name')

    def resolve_formatted_name(self, args, info):
        return self.get('formatted_name')

    def resolve_user_id(self, args, info):
        return self.get('user_id')

    def resolve_filename(self, args, info):
        return self.get('filename')

    def resolve_objective(self, args, info):
        return self.get('objective')

    def resolve_summary(self, args, info):
        return self.get('summary')

    def resolve_total_months_experience(self, args, info):
        return self.get('total_months_experience')

    def resolve_added_time(self, args, info):
        return self.get('added_time')

    def resolve_updated_datetime(self, args, info):
        return self.get('updated_datetime')

    def resolve_candidate_status_id(self, args, info):
        return self.get('candidate_status_id')

    def resolve_source_id(self, args, info):
        return self.get('source_id')

    def resolve_culture_id(self, args, info):
        return self.get('culture_id')

    # ***** Secondary attributes *****
    addresses = graphene.List(CandidateAddressType)
    emails = graphene.List(CandidateEmailType)
    educations = graphene.List(EducationType)
    phones = graphene.List(PhoneType)

    def resolve_addresses(self, args, info):
        return self.get('addresses')

    def resolve_emails(self, args, info):
        return self.get('emails')

    def resolve_educations(self, args, info):
        return self.get('educations')

    def resolve_phones(self, args, info):
        return self.get('phones')


try:
    from graphql_service.modules.query import CandidateQuery
    from mutation import CandidateMutation

    schema = graphene.Schema(query=CandidateQuery, mutation=CandidateMutation, auto_camelcase=False)
except Exception as e:
    print "Error: {}".format(e.message)
    raise InternalServerError('Unable to create schema because: {}'.format(e.message))
