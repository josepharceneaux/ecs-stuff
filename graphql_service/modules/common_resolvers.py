"""
File contains common resolvers used by graphene defined objects
See: http://docs.graphene-python.org/en/latest/types/objecttypes/#resolvers-outside-the-class
"""
__all__ = [
    'resolve_user_id',
    'resolve_total_months_experience',
    'resolve_summary',
    'resolve_source_id',
    'resolve_added_datetime',
    'resolve_candidate_status_id',
    'resolve_city',
    'resolve_comments',
    'resolve_culture_id',
    'resolve_end_month',
    'resolve_end_year',
    'resolve_first_name',
    'resolve_formatted_name',
    'resolve_is_current',
    'resolve_is_default',
    'resolve_iso3166_country',
    'resolve_iso3166_subdivision',
    'resolve_last_name',
    'resolve_middle_name',
    'resolve_objective',
    'resolve_resume_url',
    'resolve_start_month',
    'resolve_start_year',
    'resolve_state',
    'resolve_updated_datetime',
    'resolve_zip_code'
]


def resolve_added_datetime(root, args, context, info):
    return root.get('added_datetime')


def resolve_updated_datetime(root, args, context, info):
    return root.get('updated_datetime')


def resolve_is_current(root, args, context, info):
    return root.get('is_current')


def resolve_is_default(root, args, context, info):
    return root.get('is_default')


def resolve_city(root, args, context, info):
    return root.get('city')


def resolve_state(root, args, context, info):
    return root.get('state')


def resolve_iso3166_subdivision(root, args, context, info):
    return root.get('iso3166_subdivision')


def resolve_iso3166_country(root, args, context, info):
    return root.get('iso3166_country')


def resolve_zip_code(root, args, context, info):
    return root.get('zip_code')


def resolve_start_year(root, args, context, info):
    return root.get('start_year')


def resolve_start_month(root, args, context, info):
    return root.get('start_month')


def resolve_end_year(root, args, context, info):
    return root.get('end_year')


def resolve_end_month(root, args, context, info):
    return root.get('end_month')


def resolve_comments(root, args, context, info):
    return root.get('comments')


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
