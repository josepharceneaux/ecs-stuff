# -*- coding: utf-8 -*-

# To change this template, choose Tools | Templates
# and open the template in the editor.

import math
import operator
from datetime import datetime
import os
import boto
import boto.exception
import simplejson

from candidate_service.common.models.db import get_table, db, session
from sqlalchemy import select
from candidate_service.app import logger

API_VERSION = "2013-01-01"
MYSQL_DATE_FORMAT = '%Y-%m-%dT%H:%i:%S.%fZ'
BATCH_REQUEST_LIMIT_BYTES = 5 * 1024 * 1024
DOCUMENT_SIZE_LIMIT_BYTES = 1024 * 1024
CLOUDSEARCH_SDF_S3_FOLDER = "CloudSearchSDF"
CLOUDSEARCH_MAX_LIMIT = 10000

STOPWORDS = """a
an
and
are
as
at
be
but
by
for
if
in
into
is
it
no
not
of
on
or
s
such
t
that
the
their
then
there
these
they
this
to
was
will
with
"""

STOPWORDS_JSON_ARRAY = simplejson.dumps(filter(None, STOPWORDS.split()))

_cloud_search_connection_layer_2 = None

_cloud_search_domain = None
"""
:type: None | boto.cloudsearch2.domain.Domain
"""

DEFAULT_SORT_FIELD = "_score"
DEFAULT_SORT_ORDER = "desc"

"""
The boolean fields below are True by default.
Dates are in IETF RFC3339: yyyy-mm-ddTHH:mm:ss.SSSZ
"""
INDEX_FIELD_NAME_TO_OPTIONS = {
    'id':                           dict(IndexFieldType='int',              IntOptions={'FacetEnabled': False}),
    'first_name':                   dict(IndexFieldType='text',             TextOptions={'Stopwords': STOPWORDS_JSON_ARRAY,
                                                                                         'HighlightEnabled': False}),
    'last_name':                     dict(IndexFieldType='text',            TextOptions={'Stopwords': STOPWORDS_JSON_ARRAY,
                                                                                         'HighlightEnabled': False}),
    'email':                         dict(IndexFieldType='text-array'),
    'user_id':                       dict(IndexFieldType='int'),
    'domain_id':                     dict(IndexFieldType='int',             IntOptions={'ReturnEnabled': False}),
    'source_id':                     dict(IndexFieldType='int'),
    'source_product_id':             dict(IndexFieldType='int'),
    'status_id':                     dict(IndexFieldType='int'),
    'objective':                     dict(IndexFieldType='text',            TextOptions={'Stopwords': STOPWORDS_JSON_ARRAY}),
    'text_comment':                  dict(IndexFieldType='text-array',      TextArrayOptions={'ReturnEnabled': False}),
    'unidentified_description':      dict(IndexFieldType='text-array',      TextArrayOptions={'ReturnEnabled': False}),
    'custom_field_id_and_value':     dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),
    'candidate_rating_id_and_value': dict(IndexFieldType='text-array',      TextArrayOptions={'ReturnEnabled': False}),
    'area_of_interest_id':           dict(IndexFieldType='int-array',       IntArrayOptions={'ReturnEnabled': False}),
    'added_time':                    dict(IndexFieldType='date',            DateOptions={'FacetEnabled': False}),

    # Location
    'city':                          dict(IndexFieldType='text-array',      TextArrayOptions={'ReturnEnabled': False}),
    'state':                         dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),
    'zip_code':                      dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False,
                                                                                                 'SortEnabled': False}),
    'coordinates':                   dict(IndexFieldType='latlon',          LatLonOptions={'ReturnEnabled': False,
                                                                                           'FacetEnabled': False}),

    # Experience
    'total_months_experience':       dict(IndexFieldType='int',             IntOptions={'ReturnEnabled': False}),
    'organization':                  dict(IndexFieldType='text-array'),
    'position':                      dict(IndexFieldType='literal-array'),
    'experience_description':        dict(IndexFieldType='text-array',      TextArrayOptions={'ReturnEnabled': False}),
    'skill_description':             dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),

    # Education
    'degree_type':                   dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),
    'degree_title':                  dict(IndexFieldType='text-array',      TextArrayOptions={'ReturnEnabled': False}),
    'degree_end_date':               dict(IndexFieldType='date-array',      DateArrayOptions={'ReturnEnabled': False}),
    'concentration_type':            dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),
    'school_name':                   dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),

    # Military
    'military_service_status':       dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),
    'military_branch':               dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),
    'military_highest_grade':        dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False}),
    'military_end_date':             dict(IndexFieldType='date-array',      DateArrayOptions={'ReturnEnabled': False}),
}

GOOGLE_ANALYTICS_TRACKING_ID = "UA-33209718-1"
HMAC_KEY = "s!web976892"

AWS_ACCESS_KEY_ID = 'AKIAI3422SZ6SL46EYBQ'
AWS_SECRET_ACCESS_KEY = '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'

NUANCE_OMNIPAGE_CLOUD_ACCOUNT_NAME = 'Eval4Osman_20120920'
NUANCE_OMNIPAGE_CLOUD_ACCOUNT_KEY = 'n8YCzECC4N5e/S3niBIfczsw3BrSBzNeTp+8LgxvMX8='

YAHOO_PLACEFINDER_APP_ID = "KNHq6P4q"
YAHOO_PLACEFINDER_CONSUMER_KEY = "dj0yJmk9OXpNcjdhUWpzV0pxJmQ9WVdrOVMwNUljVFpRTkhFbWNHbzlNVEF4TVRFeU16ZzJNZy0tJnM9Y29uc3VtZXJzZWNyZXQmeD1iMg--"
YAHOO_PLACEFINDER_CONSUMER_SECRET = "a74651047d03802c83b06d55168486c58eac7771"

HIPCHAT_TOKEN = 'ZmNg80eCeIN6sMCjIv03KNO2B4tqRcxTQNL44FBd'

SOCIALCV_API_KEY = "c96dfb6b9344d07cee29804152f798751ae8fdee"
STACKOVERFLOW_API_KEY = "hzOEoH16*Q7Y3QCWT9y)zA(("

CLOUDSEARCH_REGION = os.environ.get('CLOUDSEARCHREGION')


def get_cloud_search_connection():
    global _cloud_search_connection_layer_2, _cloud_search_domain
    if not _cloud_search_connection_layer_2:
        _cloud_search_connection_layer_2 = boto.connect_cloudsearch2(aws_access_key_id=AWS_ACCESS_KEY_ID,
                                                                     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                                                     sign_request=True,
                                                                     region=CLOUDSEARCH_REGION)

        import TalentPropertyManager
        cloudsearch_domain_name = TalentPropertyManager.get_cloudsearch_domain_name()
        _cloud_search_domain = _cloud_search_connection_layer_2.lookup(cloudsearch_domain_name)
        if not _cloud_search_domain:
            return "Not Cloud Search Domain...!!"

    return _cloud_search_connection_layer_2


def create_domain(domain_name=None):
    """
    Creates the given domain if doesn't exist

    :param domain_name: the domain name. If none, uses the one from config
    :return: Domain object, or None if not found
    """
    if not domain_name:
        import TalentPropertyManager
        domain_name = TalentPropertyManager.get_cloudsearch_domain_name()
    layer2 = get_cloud_search_connection()
    if not layer2.lookup(domain_name):
        return layer2.create_domain(domain_name)


def make_search_service_public():
    get_cloud_search_connection()
    access_policies = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "*"
        ]
      },
      "Action": [
        "cloudsearch:search",
        "cloudsearch:suggest"
      ]
    }
  ]
}"""
    _cloud_search_connection_layer_2.layer1.update_service_access_policies(domain_name=_cloud_search_domain.name,
                                                                           access_policies=access_policies)


def _get_search_service():
    get_cloud_search_connection()
    return _cloud_search_domain.get_search_service().domain_connection


def search_candidates(domain_id, vars, search_limit=15, candidate_ids_only=False,
                      get_percentage_match=False, count_only=False):
    """
    Searches candidates based on domain_id and Vars provided.
    Search Engine: Amazon Cloud Search

    :param
        domain_id: Search candidates in given domain Id
        vars: Search criteria, or various search filters
        search_limit: @TODO
        candidate_ids_only: if true returns only dict of candidate_ids and total_found
        get_percentage_match: if true returns percentage match of result in respective to search query provided
        count_only:  @TODO

    :returns
        Dictionary consisting of:
            list of candidate_ids
            percentage_matches list of percentage match for retrieved search results, iff get_percentage_match is true
            search_data as returned from cloudsearch
            total records found
            descriptions=[] @TODO find why is this empty dictionary needed?
            max_pages @TODO

    Set search_limit = 0 for no limit, candidate_ids_only returns dict of candidate_ids.
    Parameters in 'vars' could be single values or arrays.
    """
    # Remove the [] from inputs ending with []
    for var_name in vars.keys():
        if "[]" == var_name[-2:]: vars[var_name[:-2]] = vars[var_name]

    # If source_id has product_ in it, then remove it and add product_id to filter vars
    if not vars.get('product_id') and vars.get('source_id'):
        if isinstance(vars['source_id'], basestring): # source_id is string
            if 'product_' in vars['source_id']:
                vars['product_id'] = vars['source_id'].replace('product_', '')
                vars['source_id'] = ''
        else:  # source_id is array
            new_source_ids = []
            for source_or_product in vars['source_id']:
                if 'product_' in source_or_product:  # if product id found, add to product_id array

                    if not vars['product_id']:
                        vars['product_id'] = []

                    vars['product_id'].append(source_or_product.replace('product_', ''))
                else: # otherwise, add to new product ids array
                    new_source_ids.append(source_or_product)
            vars['source_id'] = new_source_ids

    search_queries = []
    # If query is array, separate values by spaces
    if vars.get('query') and not isinstance(vars['query'], basestring):
        query = ' '.join(vars['query'])
        search_queries.append(query)
    elif vars.get('query'):
        query = vars.get('query')
        # search_queries.append(' AND '.join(query.split(' ')))  # kathleen cook -> kathleen AND cook
        search_queries.append(query)

    """ TODO check if we can use weights (^) instead of following logic
     (http://docs.aws.amazon.com/cloudsearch/latest/developerguide/weighting-fields.html)"""
    # score boosting sections
    filter_queries = []
    # If doing range search
    location = vars.get('location')
    coordinates = None
    geo_params = dict()
    """
    If you're doing radius-based searching, you must get geo-coordinates from Yahoo or db
    """
    if location:
        import re
        from common_functions import get_geo_coordinates_bounding
        location = location.strip()
        radius = vars.get('radius')
        # If zipcode and radius provided, get coordinates & do a geo search
        is_zipcode = re.match(r"^\d+$", location) is not None
        # Convert miles to kilometers, required by geo_location calculator
        # if no radius is given set default distance to 80.47 (50 miles)
        distance_in_km = float(radius)/0.62137 if radius else 80.47
        coords_dict = get_geo_coordinates_bounding(location, distance_in_km)
        if coords_dict and coords_dict.get('point'):
            coordinates = coords_dict['point']
            # if coordinates found, then only perform location search
            filter_queries.append("coordinates:['%s,%s','%s,%s']" % (coords_dict['top_left'][0],coords_dict['top_left'][1], coords_dict['bottom_right'][0],coords_dict['bottom_right'][1]))
        elif is_zipcode:

            """If coodinates were not found with given location and if location is type of zipcode,
            then search based on zipcode"""

            filter_queries.append("(term field=zip_code '%s')" % location)

    # Location based search as of solr; commenting with docstring
    """
    if location:
        import re
        from ResumeParsing import get_coordinates
        radius = vars.get('radius')
        location = location.strip()
        from TalentSearch import state_row_from_string
        state_row = state_row_from_string(location)

        if state_row:  # If location is only a state
            state_name = '"%s"' % state_row.name
            state_abbr = '"%s"' % state_row.alphaCode
            ##filter_queries.append('location:(%s)' % (' OR '.join([state_name, state_abbr])))
            filter_queries.append("(or location:'%s' '%s')" % (state_name, state_abbr))
        else:  # Otherwise, assume zipcode or City, State

            # If zipcode and radius provided, get coordinates & do a geo search
            is_zipcode = re.match(r"^\d+$", location) is not None
            if is_zipcode and radius:
                coordinates = get_coordinates(zipcode=location)
            elif is_zipcode:
                filter_queries.append("(term field=location '%s')" % location)
            else:  # Else, assume City, State. Otherwise do a normal location search
                city_state_match = re.match(r"(.+),\s*(.+)", location)
                if city_state_match:
                    city, state = city_state_match.groups()
                    state_row = state_row_from_string(state)

                    # If entered state is valid, use it, otherwise do normal location search
                    if state_row:
                        # If radius is provided, get coordinates & do geo search
                        if radius:
                            coordinates = get_coordinates(city=city, state=state_row.name)
                        else:
                            filter_queries.append('location:("%s" AND ("%s" OR "%s"))' % (city, state_row.name, state_row.alphaCode))
                    else:
                        filter_queries.append('location:("%s")' % location)

                else:  # If neither zipcode nor City, State, then just do a location search
                    filter_queries.append('location:("%s")' % location)

            # If coordinates found, set geo distance filter. Otherwise do a normal location search
            if coordinates:
                #TODO check !bbox compatibility with cloudsearch
                filter_queries.append('{!bbox}')
                radius = vars.get('radius') or 50
                geo_params = dict(sfield='coordinates', pt=coordinates, d=( float(radius) * 1.60934 ))
    """
    filter_queries.append("(term field=domain_id %s)" % domain_id)

    # Sorting
    sort = '%s %s'
    if vars.get('sort_by') and '-' in vars.get('sort_by'):
        sort_field, sort_order = vars.get('sort_by').split('-')
    else:
        sort_field, sort_order = (DEFAULT_SORT_FIELD, DEFAULT_SORT_ORDER)

    if sort_field == 'proximity':
        if coordinates:
                sort_field = 'distance'
        else:
            sort_field = DEFAULT_SORT_FIELD
            sort_order = DEFAULT_SORT_ORDER

    sort = sort % (sort_field, sort_order.lower())

    if type(vars.get('usernameFacet')) == list:
        filter_queries.append("(or %s)" % ' '.join("user_id:%s" % uid for uid in vars.get('usernameFacet') ))
    elif vars.get('usernameFacet'):
        filter_queries.append("(term field=user_id %s)" % vars.get('usernameFacet'))

    # TODO: Add areaOfInterestNameFacet logic here, we need this for legacy data on production

    if type(vars.get('areaOfInterestIdFacet')) == list:
        filter_queries.append("(or %s)" % " ".join("area_of_interest_id:%s" % aoi for aoi in vars.get('areaOfInterestIdFacet')))
    elif vars.get('areaOfInterestIdFacet'):
        filter_queries.append("(term field=area_of_interest_id  %s)" % vars.get('areaOfInterestIdFacet'))

    if type(vars.get('statusFacet')) == list:
        filter_queries.append("(or %s)" % " ".join("status_id:%s" % status_facet for status_facet in vars.get('statusFacet')))
    elif vars.get('statusFacet'):
        filter_queries.append("(term field=status_id %s)" % vars.get('statusFacet'))

    if type(vars.get('sourceFacet')) == list:
        # search for exact values in facets
        source_facets = [ "source_id:%s" % source_facet for source_facet in vars.get('sourceFacet') ]
        filter_queries.append("(or %s)" % ' '.join( source_facets ))
    elif vars.get('sourceFacet'):
        filter_queries.append("(term field=source_id %s)" % vars.get('sourceFacet'))

    # Set filter range for years experience, if given
    if vars.get('minimum_years_experience') or vars.get('maximum_years_experience'):
        min_months = int(vars.get('minimum_years_experience')) * 12 if vars.get('minimum_years_experience') else 0  #set default to 0 because * doesn't works with cloudsearch
        max_months = int(vars.get('maximum_years_experience')) * 12 if vars.get('maximum_years_experience') else 480  #set default to 480 (max for 40 years)
        filter_queries.append("(range field=total_months_experience [%s,%s])" % (min_months, max_months))

    # date filtering
    add_time_from = vars.get('date_from')
    add_time_to = vars.get('date_to')

    add_time_from = datetime.strptime(add_time_from, '%m/%d/%Y').isoformat() + 'Z' if add_time_from else None
    add_time_to = datetime.strptime(add_time_to, '%m/%d/%Y').isoformat() + 'Z' if add_time_to else None

    if add_time_from or add_time_to:
        add_time_from = "['%s'" % add_time_from if add_time_from else "{"  # following cloudsearch syntax
        add_time_to = "'%s']" % add_time_to if add_time_to else "}"
        filter_queries.append("(range field=added_time %s,%s)" % (add_time_from, add_time_to))

    if type(vars.get('positionFacet')) == list:
        # search for exact values in facets
        position_facets = [ "position:'%s'" % position_facet for position_facet in vars.get('positionFacet') ]
        filter_queries.append("(and %s)" % " ".join(position_facets))
    elif vars.get('positionFacet'):
        filter_queries.append("( term field=position '%s')" % vars.get('positionFacet'))

    if type(vars.get('skillDescriptionFacet')) == list:
        # search for exact values in facets
        skill_facets = [ "skill_description:'%s'" % skill_facet for skill_facet in vars.get('skillDescriptionFacet') ]
        filter_queries.append("(and %s )" % " ".join(skill_facets))
    elif vars.get('skillDescriptionFacet'):
        filter_queries.append("(term field=skill_description '%s')" % vars.get('skillDescriptionFacet'))

    if type(vars.get('degreeTypeFacet')) == list:
        # search for exact values in facets
        degree_facets = ["degree_type:'%s'" % degree_facet for degree_facet in vars.get('degreeTypeFacet')]
        filter_queries.append("(or %s)" % " ".join(degree_facets))
    elif vars.get('degreeTypeFacet'):
        filter_queries.append("(term field=degree_type '%s')" % vars.get('degreeTypeFacet'))

    if type(vars.get('schoolNameFacet')) == list:
        # search for exact values in facets
        school_facets = ["school_name:'%s'" % school_facet for school_facet in vars.get('schoolNameFacet')]
        filter_queries.append("(or %s)" % " ".join(school_facets))
    elif vars.get('schoolNameFacet'):
        filter_queries.append("(term field=school_name '%s')" % vars.get('schoolNameFacet'))

    if type(vars.get('concentrationTypeFacet')) == list:
        # search for exact values in facets
        concentration_facets = [ "concentration_type:'%s'" % concentration_facet for concentration_facet in vars.get('concentrationTypeFacet') ]
        filter_queries.append("(and %s)" % " ".join(concentration_facets))
    elif vars.get('concentrationTypeFacet'):
        filter_queries.append("(term field=concentration_type '%s')" % vars.get('concentrationTypeFacet'))

    if vars.get('degree_end_year_from') or vars.get('degree_end_year_to'):
        from_datetime_str, to_datetime_str = _convert_date_range_in_cloudsearch_format(vars.get('degree_end_year_from'), vars.get('degree_end_year_to'))
        if from_datetime_str is not None and to_datetime_str is not None:
            filter_queries.append("degree_end_date:%s,%s" % (from_datetime_str, to_datetime_str))

    if type(vars.get('serviceStatus')) == list:
        # search for exact values in facets
        service_status_facets = ["military_service_status:'%s'" % service_status_facet for service_status_facet in vars.get('serviceStatus')]
        filter_queries.append("(or %s)" % " ".join( service_status_facets))
    elif vars.get('serviceStatus'):
        filter_queries.append("(term field=military_service_status '%s')" % vars.get('serviceStatus'))

    if type(vars.get('branch')) == list:
        # search for exact values in facets
        branch_facets = ["military_branch:'%s'" % branch_facet for branch_facet in vars.get('branch')]
        filter_queries.append("(or %s)" % " ".join( branch_facets ))
    elif vars.get('branch'):
        filter_queries.append("(term field=military_branch '%s' )" % vars.get('branch'))

    if type(vars.get('highestGrade')) == list:
        # search for exact values in facets
        grade_facets = ["military_highest_grade:'%s'" % grade_facet for grade_facet in vars.get('highestGrade')]
        filter_queries.append("(or %s)" % " ".join( grade_facets ))
    elif vars.get('highestGrade'):
        filter_queries.append("(term field=military_highest_grade '%s')" % vars.get('highestGrade'))

    # Date of separation - Military
    if vars.get('military_end_date_from') or vars.get('military_end_date_to'):
        from_datetime_str, to_datetime_str = _convert_date_range_in_cloudsearch_format(vars.get('military_end_date_from'), vars.get('military_end_date_to'))
        if from_datetime_str is not None and to_datetime_str is not None:
            filter_queries.append("military_end_date:%s,%s" % (from_datetime_str, to_datetime_str))

    # handling custom fields
    custom_field_vars = list()
    # kaiser_custom_cities_list = list()
    """TODO we should actually use some Google geocoding/maps API to verify the City of Interest & State of Interest
    values. We should then re-implement the filtering using kaiser_custom_cities_list. We could also use their
    Places Autocomplete API on the frontend, instead."""
    city_of_interest_custom_fields = []
    for key, value in vars.items():
        if 'cf-' in key:
            cf_id = key.split('-')[1]

            # This is for handling kaiser's NUID custom field
            if int(cf_id) == 14 and value == 'Has NUID':
                cf_value = cf_id+'|'
                # filter_queries.append('custom_field_id_and_value:(%s)' % cf_value)
                filter_queries.append("(prefix field=custom_field_id_and_value '%s')" % cf_value)
                continue

            # This is for handling standard custom values (not for email preferences)
            if type(value) == list:
                # To avoid REQUEST TOO LONG error we are limiting the search to 50 items
                # TODO: When Kaiser city of interest and state of interest is merged, remove the logic to truncate to 50.
                value = value[0:50]
                for val in value:
                    cf_value = cf_id+'|'+val
                    custom_field_vars.append(cf_value)
            else:
                cf_value = cf_id+'|'+value
                custom_field_vars.append(cf_value)

    if len(custom_field_vars):
        import re
        custom_field_vars = ["'%s'" % custom_field for custom_field in custom_field_vars]

        # special case for kaiser custom fields, 38 is the custom field id = State of Interest
        city_of_interest_custom_fields_index = [i for i, x in enumerate(custom_field_vars) if re.findall(r'\"38\|(.*?)\"', x)]

        if len(city_of_interest_custom_fields_index):
            for i in sorted(city_of_interest_custom_fields_index, reverse=True):
                city_of_interest_custom_fields.append(custom_field_vars[i])
                del custom_field_vars[i]

        if len(custom_field_vars):
            custom_fields_facets = ["custom_field_id_and_value:%s" % custom_field_facet for custom_field_facet in custom_field_vars]
            filter_queries.append("(or %s)" % " ".join( custom_fields_facets ))
        if len(city_of_interest_custom_fields):
            city_of_interest_custom_fields_facets = ["custom_field_id_and_value:%s" %
                                                     city_of_interest_custom_fields_facet
                                                     for city_of_interest_custom_fields_facet
                                                     in city_of_interest_custom_fields]
            filter_queries.append("(or %s)" % " " . join(city_of_interest_custom_fields_facets))

    """
    Two funnel search modes:
    Regular search
    Advanced rating filtering
    """
    page = int(vars.get('page')) if (vars.get('page') and (int(vars.get('page')) > 0)) else 1
    offset = (page - 1) * search_limit if search_limit else 0

    if count_only:
        search_limit = 0
        offset = 0
    elif search_limit == 0 or search_limit > CLOUDSEARCH_MAX_LIMIT:
        search_limit = CLOUDSEARCH_MAX_LIMIT

    if not search_queries:
        # If no search query is provided, (may be in case of landing talent page) then fetch all results
        query_string = "id:%s" % vars['id'] if vars.get('id') else "*:*"
    else:
        query_string = "(or %s)" % " ".join(search_queries)
        if vars.get('id'):
            # If we want to check if a certain candidate ID is in a smartlist
            query_string = "(and id:%s %s)" % (vars['id'], query_string)

    params = dict(query=query_string, sort=sort, start=offset, size=search_limit)
    params['query_parser'] = 'lucene'

    if filter_queries:
        params['filter_query'] = "(and %s)" % ' '.join(filter_queries) if len(filter_queries)>1 else ' '.join(filter_queries)

    if sort_field == "distance":
        params['expr'] = "{'distance':'haversin(%s,%s,coordinates.latitude,coordinates.longitude)'}"%(coordinates[0], coordinates[1])
        params['sort'] = "distance %s" % sort_order

    # Adding facet fields parameters

    if not count_only:
        params['facet'] = "{area_of_interest_id:{size:500},source_id:{size:50}," \
                          "user_id:{size:50},status_id:{size:50},skill_description:{size:500}," \
                          "position:{size:50},school_name:{size:500},degree_type:{size:50}," \
                          "concentration_type:{size:50},military_service_status:{size:50}," \
                          "military_branch:{size:50},military_highest_grade:{size:50}," \
                          "custom_field_id_and_value:{size:1000}}"

    if len(geo_params):
        params = dict(params.items() + geo_params.items())

    # Return data dictionary. Initializing here, to have standard return type across the function
    context_data = dict(candidate_ids=[],
                        percentage_matches=[],
                        search_data=dict(descriptions=[], facets=dict(), error=dict(), vars=vars, mode='search'),
                        total_found=0,
                        descriptions=[],
                        max_score=0,
                        max_pages=0)

    # Looks like cloudsearch does not have something like return only count predefined
    # removing fields and returned content should speed up network request
    if count_only:
        params['ret'] = "_no_fields,_score"
        params['size'] = 0
    else:
        params['ret'] = "_all_fields,_score"

    # If only candidate id is required then return candidate ids and total candidates found.
    if search_limit >= CLOUDSEARCH_MAX_LIMIT and candidate_ids_only:  # Max cloudsearch search limit, then implement cursor (paging beyond 10000 limit)
        candidate_ids, total_found, error = _cloud_search_fetch_all(params)
        if error:
            return context_data
        return dict(total_found=total_found, candidate_ids=candidate_ids)

    # Make search request with error handling
    import time
    start_time = time.time()
    search_service = _get_search_service()
    try:
        results = search_service.search(**params)
    except Exception:
        return context_data

    matches = results['hits']['hit']

    total_found = results['hits']['found']

    if count_only:
        return dict(total_found=total_found, candidate_ids=[])

    candidate_ids = [ match.get('id') for match in matches ]

    if candidate_ids_only:
        return dict(total_found=total_found, candidate_ids=candidate_ids)

    facets = get_faceting_information(results.get('facets'),domain_id)

    # Update facets
    _update_facet_counts(filter_queries,params['filter_query'], facets, query_string, domain_id)

    for facet_field_name, facet_dict in facets.iteritems():
        facets[facet_field_name] = sorted(facet_dict.iteritems(), key=operator.itemgetter(1), reverse=True)

    # Special flag for kaiser's NUID custom field
    has_kaiser_nuid = False
    num_kaiser_nuids = 0
    if len(facets.get('custom_field_id_and_value',dict())):
        custom_fields = dict()
        for cf_facet_row in facets['custom_field_id_and_value']:
            # cf_hash example: 9|Top Gun
            # 9 = id of custom field (in this case, Movies)
            # right side of | is the value of that custom field
            cf_hash = cf_facet_row[0]
            cf_id = cf_hash.split('|')[0]
            cf_value = cf_hash.split('|')[1]
            cf_facet_count = cf_facet_row[1]

            """
            If the cf_id is 14 (NUID's for Kaiser),
                Do not add values to the custom_fields list,
                they just want facets for whether the candidate has a NUID or not

                Since cf_id 14 is requested as a facet, we'll handle it as a special case:
                facet.query={!ex=dt key="has NUID"}customFieldKP:14|*
            """
            if int(cf_id) == 14:
                has_kaiser_nuid = True
                num_kaiser_nuids += cf_facet_count
                continue

            if not custom_fields.get('cf-'+cf_id):
                custom_fields['cf-'+cf_id] = list()

            custom_fields['cf-'+cf_id].append( (cf_value, cf_facet_count) )

        if has_kaiser_nuid:
            custom_fields['cf-14'] = [('Has NUID', num_kaiser_nuids)]

        facets = dict( facets.items() + custom_fields.items() )

    # Get max score
    max_score = 1
    if get_percentage_match:
        # if sorting is other than "_score, desc", fire another query with _score, desc sorting so as to get
        # max relevance score.
        default_sorting = "%s %s" %(DEFAULT_SORT_FIELD, DEFAULT_SORT_ORDER)
        params['sort'] = default_sorting  # Update the sort parameter, to have sorting based on _score, desc
        # Limit search to one result, we only want max_score which is top most row when sorted with above criteria
        params['size'] = 1
        params['ret'] = "_score"
        params['start'] = 0
        params.pop("facet", None)
        single_result = search_service.search(**params)
        # single_result = single_response.json()
        single_hit = single_result['hits']['hit']
        if len(single_hit) > 0:
            max_score = single_hit[0]['fields']['_score']

    percentage_matches = []

    search_data = dict(descriptions=matches, facets=facets, error=dict(), vars=vars, mode='search')

    max_pages = int(math.ceil(total_found / float(search_limit))) if search_limit else 1

    # Update return dictionary with search results
    context_data['candidate_ids'] = candidate_ids
    context_data['percentage_matches'] = percentage_matches
    context_data['search_data'] = search_data
    context_data['total_found'] = total_found
    context_data['descriptions'] = []
    context_data['max_score'] = max_score
    context_data['max_pages'] = max_pages

    return context_data


def get_faceting_information(facets, domain_id):
    # Fetch facet names from database with given ids
    search_facets_values = {}
    # cache = SimpleCache()
    facet_aoi = facets.get('area_of_interest_id').get('buckets')  # db area_of_interest_id
    facet_owner = facets.get('user_id').get('buckets')  # db user
    facet_source = facets.get('source_id').get('buckets')  # db candidate_source
    facet_status = facets.get('status_id').get('buckets')  # db candidate_status
    facet_skills = facets.get('skill_description').get('buckets')  # skills
    facet_position = facets.get('position').get('buckets')  # position = job_title
    facet_university = facets.get('school_name').get('buckets')  # university = school_name
    facet_degree_type = facets.get('degree_type').get('buckets')  # degree = degree_type
    facet_major = facets.get('concentration_type').get('buckets')  # major = concentration_type
    facet_military_service_status = facets.get('military_service_status').get('buckets')
    facet_military_branch = facets.get('military_branch').get('buckets')
    facet_military_highest_grade = facets.get('military_highest_grade').get('buckets')
    facet_custom_field_id_and_value = facets.get('custom_field_id_and_value').get('buckets')

    if facet_owner:
        search_facets_values['usernameFacet'] = get_username_facet_info_with_ids(facet_owner)

    if facet_aoi:
        search_facets_values['areaOfInterestIdFacet'] = get_facet_info_with_ids('area_of_interest', facet_aoi,
                                                                                'description')

    if facet_source:
        search_facets_values['sourceFacet'] = get_facet_info_with_ids('candidate_source', facet_source,
                                                                      'description')

    if facet_status:
        search_facets_values['statusFacet'] = get_facet_info_with_ids('candidate_status', facet_status,
                                                                      'description')

    if facet_skills:
        search_facets_values['skillDescriptionFacet'] = get_bucket_facet_value_count(facet_skills)

    if facet_position:
        search_facets_values['positionFacet'] = get_bucket_facet_value_count(facet_position)

    if facet_university:
        search_facets_values['schoolNameFacet'] = get_bucket_facet_value_count(facet_university)

    if facet_degree_type:
        search_facets_values['degreeTypeFacet'] = get_bucket_facet_value_count(facet_degree_type)

    if facet_major:
        search_facets_values['concentrationTypeFacet'] = get_bucket_facet_value_count(facet_major)

    if facet_military_service_status:
        search_facets_values['serviceStatus'] = get_bucket_facet_value_count(facet_military_service_status)

    if facet_military_branch:
        search_facets_values['branch'] = get_bucket_facet_value_count(facet_military_branch)

    if facet_military_highest_grade:
        search_facets_values['highestGrade'] = get_bucket_facet_value_count(facet_military_highest_grade)

    # TODO: productFacet, customFieldKP facets are remaining, how to do it?
    if facet_custom_field_id_and_value:
        search_facets_values['custom_field_id_and_value'] = get_bucket_facet_value_count(facet_custom_field_id_and_value)

    return search_facets_values


def get_username_facet_info_with_ids(facet_owner):
    tmp_dict = get_facet_info_with_ids('user', facet_owner, 'email')
    # Dict is (email, value) -> count
    new_tmp_dict = dict()
    # Replace each user's email with name
    for email_value_tuple, count in tmp_dict.items():
        c_source = get_table('user')
        user_row = session.query(c_source).filter_by(email=email_value_tuple[0]).first()
        # user = users.find(lambda u: u.email == email_value_tuple[0]).first()
        new_tmp_dict[user_row.firstName+" "+user_row.lastName, email_value_tuple[1]] = count
    return new_tmp_dict


def get_facet_info_with_ids(table_name, facet, field_name):
    """
    Few facets are filtering using ids, for those facets with ids, get their names (from db) for displaying on html
    also send ids so as to ease search with filter queries,
    returned ids will serve as values to checkboxes.
    :param facet: Facet as received from cloudsearch (bucket value contains id of facet)
    :param field_name: Name which is to be returned for UI. This is name of field from table
    :return: Dictionary with field name as key and count of candidates + facet id as value
    """

    tmp_dict = {}
    for bucket in facet:
        table = get_table(table_name)
        row = session.query(table).filter_by(id=int(bucket['value'])).first()
        if row:
            tmp_dict[(getattr(row, field_name), bucket['value'])] = bucket['count']
        else:
            pass

    return tmp_dict


def get_bucket_facet_value_count(facet):
    """
    This function is specifically for those facets which are having proper values not ids(which need database query)
    Collects list of dictionaries having value and count and return single dictionary with value, count pair
    :param facet (type-List of dicts): single facet of facets returned from cloudsearch (contains count and value dicts)
    eg: {u'buckets': [{u'count': 5, u'value': u'Bachelors'}, {u'count': 3, u'value': u'Masters'}]}
    :return: dictionary with value as key and count as value
    eg: {'Bachelors':5, 'Masters':3}
    """
    tmp_dict = {}
    for bucket in facet:
        tmp_dict[bucket['value']] = bucket['count']
    return tmp_dict


def _update_facet_counts(filter_queries, params_fq, existing_facets, query_string, domain_id):
    """
    For multi-select facets, return facet count and values based on filter queries
    :param filter_queries:
    :return:
    """
    search_service = _get_search_service()
    # Multi-select facet scenario
    for filter_query in filter_queries:
        if 'user_id' in filter_query:
            fq_without_user_id = params_fq.replace(filter_query,'')
            query_user_id_facet = {'query': query_string, 'size': 0, 'filter_query': fq_without_user_id,
                                   'query_parser': 'lucene', 'ret': '_no_fields', 'facet': "{user_id: {size:50}}"}
            result_user_id_facet = search_service.search(**query_user_id_facet)
            facet_owner = result_user_id_facet['facets']['user_id']['buckets']
            existing_facets['usernameFacet'] = get_username_facet_info_with_ids(facet_owner)

        if 'area_of_interest_id' in filter_query:
            fq_without_area_of_interest = params_fq.replace(filter_query,'')
            query_area_of_interest_facet = {'query': query_string, 'size': 0,
                                            'filter_query': fq_without_area_of_interest, 'query_parser': 'lucene',
                                            'ret': '_no_fields', 'facet': "{area_of_interest_id: {size:500}}"}
            result_area_of_interest_facet = search_service.search(**query_area_of_interest_facet)
            facet_aoi = result_area_of_interest_facet['facets']['area_of_interest_id']['buckets']
            existing_facets['areaOfInterestIdFacet'] = get_facet_info_with_ids("area_of_interest", facet_aoi,
                                                                               'description')
        if 'source_id' in filter_query:
            fq_without_source_id = params_fq.replace(filter_query, '')
            query_source_id_facet = {'query':query_string, 'size':0, 'filter_query':fq_without_source_id, 'query_parser': 'lucene', 'ret':'_no_fields', 'facet':"{source_id: {size:50}}"}
            result_source_id_facet = search_service.search(**query_source_id_facet)
            # domain_candidate_source = db(db.candidate_source.domainId == domain_id).select(cache=(cache.ram, 120))
            facet_source = result_source_id_facet['facets']['source_id']['buckets']
            existing_facets['sourceFacet'] = get_facet_info_with_ids('candidate_source', facet_source, 'description')

        if 'school_name' in filter_query:
            fq_without_school_name = params_fq.replace(filter_query, '')
            query_school_name_facet = {'query': query_string, 'size':0, 'filter_query': fq_without_school_name,
                                       'query_parser': 'lucene', 'ret': '_no_fields',
                                       'facet': "{school_name: {size:500}}"}
            result_school_name_facet = search_service.search(**query_school_name_facet)
            facet_school = result_school_name_facet['facets']['school_name']['buckets']
            existing_facets['schoolNameFacet'] = get_bucket_facet_value_count(facet_school)
        if 'degree_type' in filter_query:
            fq_without_degree_type = params_fq.replace(filter_query,'')
            query_degree_type_facet = {'query': query_string, 'size': 0, 'filter_query': fq_without_degree_type,
                                       'query_parser': 'lucene', 'ret': '_no_fields', 'facet':
                                           "{degree_type: {size:50}}"}
            result_degree_type_facet = search_service.search(**query_degree_type_facet)
            facet_degree_type = result_degree_type_facet['facets']['degree_type']['buckets']
            existing_facets['degreeTypeFacet'] = get_bucket_facet_value_count(facet_degree_type)


def _cloud_search_fetch_all(params):
    """ Fetches all candidates from cloudsearch using cursor i.e. when search is more than 10000 candidates
    :param params: search params
    :return: candidate_ids:all candidate ids,
    :return: total_found: total number of candidate found
    :return: error: if there was error while executing search query
    """
    search_service = _get_search_service()
    params['cursor'] = 'initial'  # Initialize cursor
    # remove start, as it is produces error with cursor
    del params['start']
    no_more_candidates = False
    total_found = 0
    candidate_ids = []
    error = False
    start = 0
    # If size is more than 10000, cloudsearch will give error, so set size to chunk of 10000 candidates and fetch all
    if params['size'] > CLOUDSEARCH_MAX_LIMIT:
        params['size'] = CLOUDSEARCH_MAX_LIMIT
    while not no_more_candidates:
        # Get the next batch of candidates
        results = search_service.search(**params)
        total_found = results['hits']['found']
        start = results['hits']['start']
        matches = results['hits']['hit']
        candidate_ids.extend([match.get('id') for match in matches])

        # Update cursor for next run
        new_cursor = results['hits']['cursor']
        params['cursor'] = new_cursor

        if start == total_found:
            no_more_candidates = True

    return candidate_ids, total_found, error


def _convert_date_range_in_cloudsearch_format(from_date, to_date):
    from_datetime_str = to_datetime_str = None
    if from_date:
        try:
            from_datetime = datetime(year=int(from_date), month=1, day=1)
            from_datetime_str = "['%s'" % (from_datetime.isoformat("T") + "Z")
        except Exception:
            logger.exception("Received invalid degree_end_year_from: %s", from_date)
    else:
        # If end_year_from is not set, set to earliest possible date
        from_datetime_str = '{'

    if to_date:
        try:
            to_datetime = datetime(year=int(to_date), month=12, day=31)
            to_datetime_str = "'%s']" % (to_datetime.isoformat("T") + "Z")
        except Exception:
            logger.exception("Received invalid degree_end_year_to: %s", to_date)
    else:
        # If end_year_to is not set, set to latest possible date
        to_datetime_str = '}'
    return from_datetime_str, to_datetime_str



