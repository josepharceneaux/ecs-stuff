import graphene

# Error handling
from graphql_service.common.error_handling import InternalServerError

# Common resolvers
from common_resolvers import (
    resolve_added_datetime, resolve_is_current, resolve_city,
    resolve_end_month, resolve_end_year, resolve_iso3166_country,
    resolve_iso3166_subdivision, resolve_start_month, resolve_start_year,
    resolve_updated_datetime, resolve_is_default, resolve_zip_code,
    resolve_state, resolve_comments
)


class CandidateAddressType(graphene.ObjectType):
    name = 'CandidateAddress'

    address_line_1 = graphene.String()
    address_line_2 = graphene.String()
    city = graphene.String(resolver=resolve_city)
    state = graphene.String(resolver=resolve_state)
    zip_code = graphene.String(resolver=resolve_zip_code)
    po_box = graphene.String()
    is_default = graphene.Boolean(resolver=resolve_is_default)
    coordinates = graphene.String()
    updated_time = graphene.String(resolver=resolve_updated_datetime)
    iso3166_subdivision = graphene.String(resolver=resolve_iso3166_subdivision)
    iso3166_country = graphene.String(resolver=resolve_iso3166_country)

    def resolve_address_line_1(self, args, context, info):
        return self.get('address_line_1')

    def resolve_address_line_2(self, args, context, info):
        return self.get('address_line_2')

    def resolve_po_box(self, args, context, info):
        return self.get('po_box')

    def resolve_coordinates(self, args, context, info):
        return self.get('coordinates')


class EducationDegreeType(graphene.ObjectType):
    name = 'EducationDegreeType'

    degree_type = graphene.String()
    degree_title = graphene.String()
    start_year = graphene.Int(resolver=resolve_start_year)
    start_month = graphene.Int(resolver=resolve_start_month)
    end_year = graphene.Int(resolver=resolve_end_year)
    end_month = graphene.Int(resolver=resolve_end_month)
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)
    gpa = graphene.Float()
    comments = graphene.String(resolver=resolve_comments)
    major = graphene.String()

    def resolve_degree_type(self, args, context, info):
        return self.get('degree_type')

    def resolve_degree_title(self, args, context, info):
        return self.get('degree_title')

    def resolve_gpa(self, args, context, info):
        return self.get('gpa')

    def resolve_major(self, args, context, info):
        return self.get('major')


class EducationType(graphene.ObjectType):
    name = 'EducationType'

    school_name = graphene.String()
    school_type = graphene.String()
    city = graphene.String(resolver=resolve_city)
    state = graphene.String(resolver=resolve_state)
    iso3166_subdivision = graphene.String(resolver=resolve_iso3166_subdivision)
    is_current = graphene.Boolean(resolver=resolve_is_current)
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)

    # Nested data
    degrees = graphene.List(EducationDegreeType)

    def resolve_school_name(self, args, context, info):
        return self.get('school_name')

    def resolve_school_type(self, args, context, info):
        return self.get('school_type')

    def resolve_degrees(self, args, context, info):
        return self.degrees


class CandidateEmailType(graphene.ObjectType):
    name = 'CandidateEmail'

    address = graphene.String()
    label = graphene.String()
    is_default = graphene.Boolean(resolver=resolve_is_default)

    def resolve_label(self, args, context, info):
        return self.get('label')

    def resolve_address(self, args, context, info):
        return self.get('address')


class ExperienceType(graphene.ObjectType):
    name = 'ExperienceType'

    organization = graphene.String()
    position = graphene.String()
    city = graphene.String(resolver=resolve_city)
    iso3166_subdivision = graphene.String(resolver=resolve_iso3166_subdivision)
    iso3166_country = graphene.String(resolver=resolve_iso3166_country)
    start_year = graphene.Int(resolver=resolve_start_year)
    start_month = graphene.Int(resolver=resolve_start_month)
    end_year = graphene.Int(resolver=resolve_end_year)
    end_month = graphene.Int(resolver=resolve_end_month)
    is_current = graphene.Boolean(resolver=resolve_is_current)
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    description = graphene.String()

    def resolve_organization(self, args, context, info):
        return self.get('organization')

    def resolve_position(self, args, context, info):
        return self.get('position')


class MilitaryServiceType(graphene.ObjectType):
    name = 'MilitaryServiceType'

    service_status = graphene.String()
    highest_rank = graphene.String()
    highest_grade = graphene.String()
    branch = graphene.String()
    comments = graphene.String(resolver=resolve_comments)
    start_year = graphene.String(resolver=resolve_start_year)
    start_month = graphene.String(resolver=resolve_start_month)
    end_year = graphene.String(resolver=resolve_end_year)
    end_month = graphene.String(resolver=resolve_end_month)
    iso3166_country = graphene.String(resolver=resolve_iso3166_country)

    def resolve_service_status(self, args, context, info):
        return self.get('service_status')

    def resolve_highest_rank(self, args, context, info):
        return self.get('highest_rank')

    def resolve_highest_grade(self, args, context, info):
        return self.get('highest_grade')

    def resolve_branch(self, args, context, info):
        return self.get('branch')


class NoteType(graphene.ObjectType):
    name = 'NoteType'

    comments = graphene.String(resolver=resolve_comments)
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)
    title = graphene.String()
    owner_user_id = graphene.String()

    def resolve_title(self, args, context, info):
        return self.get('title')

    def resolve_owner_user_id(self, args, context, info):
        return self.get('owner_user_id')


class PhotoType(graphene.ObjectType):
    name = 'PhotoType'

    image_url = graphene.String()
    is_default = graphene.Boolean(resolver=resolve_is_default)
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)

    def resolve_image_url(self, args, context, info):
        return self.get('image_url')


class PreferredLocationType(graphene.ObjectType):
    name = 'PreferredLocationType'

    city = graphene.String(resolver=resolve_city)
    iso3166_subdivision = graphene.String(resolver=resolve_iso3166_subdivision)
    iso3166_country = graphene.String(resolver=resolve_iso3166_country)
    zip_code = graphene.String(resolver=resolve_zip_code)
    added_datetime = graphene.String(resolver=resolve_added_datetime)


class ReferenceType(graphene.ObjectType):
    name = 'ReferenceType'

    person_name = graphene.String()
    position_title = graphene.String()
    comments = graphene.String(resolver=resolve_comments)
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)

    def resolve_person_name(self, args, context, info):
        return self.get('person_name')

    def resolve_position_title(self, args, context, info):
        return self.get('position_title')


class SkillType(graphene.ObjectType):
    name = 'SkillType'

    description = graphene.String()
    total_months_used = graphene.Int()
    last_used_year = graphene.Int()
    last_used_month = graphene.Int()
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)

    def resolve_description(self, args, context, info):
        return self.get('description')

    def resolve_total_months_used(self, args, context, info):
        return self.get('total_months_used')

    def resolve_last_used_year(self, args, contect, info):
        return self.get('last_used_year')

    def resolve_last_used_month(self, args, context, info):
        return self.get('last_used_month')


class SocialNetworkType(graphene.ObjectType):
    name = 'SocialNetworkType'

    social_network_name = graphene.String()
    profile_url = graphene.String()
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)

    def resolve_social_network_name(self, args, context, info):
        return self.get('social_network_name')

    def resolve_profile_url(self, args, context, info):
        return self.get('profile_url')


class TagType(graphene.ObjectType):
    name = 'TagType'

    tag_name = graphene.String()
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)

    def resolve_tag_name(self, args, context, info):
        return self.get('tag_name')


class WorkPreferenceType(graphene.ObjectType):
    name = 'WorkPreferenceType'

    relocate = graphene.Boolean()
    authorization = graphene.String()
    telecommute = graphene.Boolean()
    travel_percentage = graphene.Int()
    hourly_rate = graphene.Float()
    salary = graphene.Int()
    tax_terms = graphene.String()
    security_clearance = graphene.Boolean()
    third_party = graphene.Boolean()

    def resolve_relocate(self, args, context, info):
        return self.get('relocate')

    def resolve_authorization(self, args, context, info):
        return self.get('authorization')

    def resolve_telecommute(self, args, context, info):
        return self.get('telecommute')

    def resolve_travel_percentage(self, args, context, info):
        return self.get('travel_percentage')

    def resolve_hourly_rate(self, args, context, info):
        return self.get('hourly_rate')

    def resolve_salary(self, args, context, info):
        return self.get('salary')

    def resolve_tax_terms(self, args, context, info):
        return self.get('tax_terms')

    def resolve_security_clearance(self, args, context, info):
        return self.get('security_clearance')

    def resolve_third_party(self, args, context, info):
        return self.get('third_party')


class PhoneType(graphene.ObjectType):
    name = 'PhoneType'

    value = graphene.String()
    label = graphene.String()
    is_default = graphene.Boolean(resolver=resolve_is_default)

    def resolve_value(self, args, context, info):
        return self.get('value')

    def resolve_label(self, args, context, info):
        return self.get('label')


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
    resume_url = graphene.String()
    objective = graphene.String()
    summary = graphene.String()
    total_months_experience = graphene.Int()
    added_datetime = graphene.String(resolver=resolve_added_datetime)
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)
    candidate_status_id = graphene.Int()
    source_id = graphene.Int()
    culture_id = graphene.Int()

    # Resolvers for candidate's primary attributes
    def resolve_first_name(self, args, context, info):
        return self.get('first_name')

    def resolve_middle_name(self, args, context, info):
        return self.get('middle_name')

    def resolve_last_name(self, args, context, info):
        return self.get('last_name')

    def resolve_formatted_name(self, args, context, info):
        return self.get('formatted_name')

    def resolve_user_id(self, args, context, info):
        return self.get('user_id')

    def resolve_resume_url(self, args, context, info):
        return self.get('resume_url')

    def resolve_objective(self, args, context, info):
        return self.get('objective')

    def resolve_summary(self, args, context, info):
        return self.get('summary')

    def resolve_total_months_experience(self, args, context, info):
        return self.get('total_months_experience')

    def resolve_candidate_status_id(self, args, context, info):
        return self.get('candidate_status_id')

    def resolve_source_id(self, args, context, info):
        return self.get('source_id')

    def resolve_culture_id(self, args, context, info):
        return self.get('culture_id')

    # ***** Secondary attributes *****
    # areas_of_interest = graphene.List(AreaOfInterestType)
    addresses = graphene.List(CandidateAddressType)
    # custom_fields = graphene.List(CustomFieldType)
    educations = graphene.List(EducationType)
    emails = graphene.List(CandidateEmailType)
    experiences = graphene.List(ExperienceType)

    military_service = graphene.List(MilitaryServiceType)
    notes = graphene.List(NoteType)
    phones = graphene.List(PhoneType)
    photos = graphene.List(PhotoType)
    preferred_locations = graphene.List(PreferredLocationType)
    references = graphene.List(ReferenceType)
    skills = graphene.List(SkillType)
    social_networks = graphene.List(SocialNetworkType)
    tags = graphene.List(TagType)
    work_preference = graphene.Field(WorkPreferenceType)

    def resolve_edits(self, args, context, info):
        return self.get('edits')

    # Resolvers for candidate's secondary attributes
    def resolve_areas_of_interest(self, args, context, info):
        return self.get('areas_of_interest')

    def resolve_addresses(self, args, context, info):
        return self.get('addresses')

    def resolve_custom_fields(self, args, context, info):
        return self.get('custom_fields')

    def resolve_educations(self, args, context, info):
        return self.get('educations')

    def resolve_emails(self, args, context, info):
        return self.get('emails')

    def resolve_experiences(self, args, context, info):
        return self.get('experiences')

    def resolve_military_services(self, args, context, info):
        return self.get('military_services')

    def resolve_notes(self, args, context, info):
        return self.get('notes')

    def resolve_phones(self, args, context, info):
        return self.get('phones')

    def resolve_photos(self, args, context, info):
        return self.get('photos')

    def resolve_preferred_locations(self, args, context, info):
        return self.get('preferred_locations')

    def resolve_references(self, args, context, info):
        return self.get('references')

    def resolve_skills(self, args, context, info):
        return self.get('skills')

    def resolve_social_networks(self, args, context, info):
        return self.get('social_networks')

    def resolve_tags(self, args, context, info):
        return self.get('tags')

    def resolve_work_preference(self, args, context, info):
        return self.get('work_preference')

    def resolve_edits(self, args, context, info):
        return self.get('edits')


try:
    from graphql_service.modules.query import CandidateQuery
    from mutation import Mutation

    schema = graphene.Schema(query=CandidateQuery, mutation=Mutation, auto_camelcase=False)
except Exception as e:
    print "Error: {}".format(e.message)
    raise InternalServerError('Unable to create schema because: {}'.format(e.message))
