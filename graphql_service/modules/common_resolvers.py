"""
File contains common resolvers used by graphene defined objects
See: http://docs.graphene-python.org/en/latest/types/objecttypes/#resolvers-outside-the-class
"""


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
