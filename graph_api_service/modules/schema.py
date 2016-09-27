import graphene

# Flask specific
from flask import request

# Error handling
from graph_api_service.common.error_handling import InternalServerError


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


class DegreeBulletType(graphene.ObjectType):
    name = 'DegreeBullet'

    id = graphene.Int()
    concentration_type = graphene.String()
    comments = graphene.String()
    added_time = graphene.String()
    updated_time = graphene.String()


class EducationDegreeType(graphene.ObjectType):
    name = 'EducationDegree'

    id = graphene.Int()
    degree_type = graphene.String()
    degree_title = graphene.String()
    start_year = graphene.Int()
    start_month = graphene.Int()
    end_year = graphene.Int()
    end_month = graphene.Int()
    gpa = graphene.Float()
    added_time = graphene.String()
    updated_time = graphene.String()

    # Nested data
    bullets = graphene.List(DegreeBulletType)

    def resolve_bullets(self, args, info):
        return self.bullets


class CandidateEducationType(graphene.ObjectType):
    name = 'CandidateEducation'

    id = graphene.Int()
    school_name = graphene.String()
    school_type = graphene.String()
    city = graphene.String()
    state = graphene.String()
    is_current = graphene.Boolean()
    added_time = graphene.String()
    updated_time = graphene.String()

    # Nested data
    degrees = graphene.List(EducationDegreeType)

    def resolve_degrees(self, args, info):
        return self.degrees


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
    added_time = graphene.String()
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

    # educations = List(CandidateEducationType)

    def resolve_addresses(self, args, info):
        return self.addresses

    def resolve_emails(self, args, info):
        return self.get('emails')

    # def resolve_educations(self, args, info):
    #     return self.get('educations')


try:
    from graph_api_service.modules.query import QueryCandidate
    from mutation import CandidateMutation

    schema = graphene.Schema(query=QueryCandidate, mutation=CandidateMutation)
except Exception as e:
    print "Error: {}".format(e.message)
    raise InternalServerError('Unable to create schema because: {}'.format(e.message))
