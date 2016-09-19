import graphene

# Flask specific
from flask import request

# Error handling
from graph_api_service.common.error_handling import InternalServerError


class CandidateAddressType(graphene.ObjectType):
    name = 'CandidateAddress'

    id = graphene.Int()
    address_line_1 = graphene.String()
    address_line_2 = graphene.String()
    city = graphene.String()
    state = graphene.String()
    zip_code = graphene.String()
    po_box = graphene.String()
    is_default = graphene.Boolean()
    coordinates = graphene.String()
    updated_time = graphene.String()  # Todo: update name to 'updated_datetime' & format timezones
    iso3166_subdivision = graphene.String()
    iso3166_country = graphene.String()


class CandidateEmailType(graphene.ObjectType):
    name = 'CandidateEmail'

    id = graphene.Int()
    address = graphene.String()
    email_label = graphene.String()
    is_default = graphene.Boolean()

    labels_mapping = {1: 'Primary', 2: 'Home', 3: 'Work', 4: 'Other'}

    def resolve_email_label(self, args, info):
        for label_id, label in self.labels_mapping.iteritems():
            if self.email_label == label:
                return label
        return 'Other'


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

    # ***** Secondary attributes *****
    addresses = graphene.List(CandidateAddressType)
    emails = graphene.List(CandidateEmailType)
    educations = graphene.List(CandidateEducationType)

    # ***** Resolvers *****
    def resolve_addresses(self, args, info):
        """
        Will return all of candidate's addresses using SQLAlchemy's relationships
        """
        return self.addresses

    def resolve_emails(self, args, info):
        """
        Will return all of candidate's emails using SQLAlchemy's relationships
        """
        return self.emails

    def resolve_educations(self, args, info):
        """
        Will return all of candidate's educations using SQLAlchemy's relationships
        """
        return self.educations


try:
    from graph_api_service.modules.query import QueryType
    from mutation import CandidateMutation

    schema = graphene.Schema(query=QueryType, mutation=CandidateMutation)
except Exception as e:
    print "NO WORK!"
    raise InternalServerError('Unable to create schema because: {}'.format(e.message))
