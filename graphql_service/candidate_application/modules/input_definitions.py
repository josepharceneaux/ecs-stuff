import graphene

__all__ = [
    'AreaOfInterestInput',
    'AddressInput',
    'CustomFieldInput',
    'EmailInput',
    'EducationDegreeInput',
    'EducationInput',
    'ExperienceInput',
    'MilitaryServiceInput',
    'NoteInput',
    'PhoneInput',
    'PhotoInput',
    'PreferredLocationInput',
    'ReferenceInput',
    'SkillInput',
    'SocialNetworkInput',
    'TagInput',
    'WorkPreferenceInput'
]


class AreaOfInterestInput(graphene.InputObjectType):
    area_of_interest_id = graphene.Int(required=True)


class AddressInput(graphene.InputObjectType):
    address_line_1 = graphene.String()
    address_line_2 = graphene.String()
    city = graphene.String()
    state = graphene.String()
    zip_code = graphene.String()
    po_box = graphene.String()
    is_default = graphene.Boolean(required=True)
    coordinates = graphene.String()
    updated_time = graphene.String()
    iso3166_subdivision = graphene.String()
    iso3166_country = graphene.String()


class CustomFieldInput(graphene.InputObjectType):
    custom_field_id = graphene.Int(required=True)
    value = graphene.String(required=True)


class EmailInput(graphene.InputObjectType):
    address = graphene.String()
    label = graphene.String()
    is_default = graphene.Boolean(required=True)


class EducationDegreeInput(graphene.InputObjectType):
    title = graphene.String()
    start_year = graphene.Int()
    start_month = graphene.Int()
    end_year = graphene.Int()
    end_month = graphene.Int()
    gpa = graphene.Float()
    concentration = graphene.String()
    comments = graphene.String()


class EducationInput(graphene.InputObjectType):
    school_name = graphene.String()
    school_type = graphene.String()
    city = graphene.String()
    state = graphene.String()
    iso3166_subdivision = graphene.String()
    is_current = graphene.Boolean(required=True)

    # Nested data
    degrees = graphene.List(EducationDegreeInput)


class ExperienceInput(graphene.InputObjectType):
    organization = graphene.String()
    position = graphene.String()
    city = graphene.String()
    iso3166_subdivision = graphene.String()
    iso3166_country = graphene.String()
    state = graphene.String()
    start_year = graphene.Int()
    start_month = graphene.Int()
    end_year = graphene.Int()
    end_month = graphene.Int()
    is_current = graphene.Boolean(required=True)
    description = graphene.String()


class MilitaryServiceInput(graphene.InputObjectType):
    service_status = graphene.String()
    highest_rank = graphene.String()
    highest_grade = graphene.String()
    branch = graphene.String()
    comments = graphene.String()
    start_year = graphene.Int()
    start_month = graphene.Int()
    end_year = graphene.Int()
    end_month = graphene.Int()
    iso3166_country = graphene.String()


class NoteInput(graphene.InputObjectType):
    title = graphene.String()
    comments = graphene.String(required=True)


class PhoneInput(graphene.InputObjectType):
    label = graphene.String()
    value = graphene.String()
    is_default = graphene.Boolean(required=True)


class PhotoInput(graphene.InputObjectType):
    image_url = graphene.String()
    is_default = graphene.Boolean(required=True)


class PreferredLocationInput(graphene.InputObjectType):
    iso3166_country = graphene.String()
    iso3166_subdivision = graphene.String()
    city = graphene.String()
    state = graphene.String()
    zip_code = graphene.String()


class ReferenceInput(graphene.InputObjectType):
    person_name = graphene.String()
    position_title = graphene.String()
    comments = graphene.String()


class SkillInput(graphene.InputObjectType):
    name = graphene.String()
    total_months_used = graphene.Int()
    last_used_year = graphene.Int()
    last_used_month = graphene.Int()


class SocialNetworkInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    profile_url = graphene.String(required=True)


class TagInput(graphene.InputObjectType):
    name = graphene.String(required=True)


class WorkPreferenceInput(graphene.InputObjectType):
    relocate = graphene.Boolean()
    authorization = graphene.String()
    telecommute = graphene.Boolean()
    travel_percentage = graphene.Int()
    hourly_rate = graphene.Float()
    salary = graphene.Int()
    tax_terms = graphene.String()
    security_clearance = graphene.String()
    third_party = graphene.Boolean()
    employment_type = graphene.String()
