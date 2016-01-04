import math
# import operator
import os
import time
import re
import boto
import boto.exception
import simplejson

from copy import deepcopy
from datetime import datetime
from flask import request
from flask import current_app
from candidate_service.candidate_app import db, logger
from candidate_service.common.models.candidate import Candidate, CandidateSource, CandidateStatus
from candidate_service.common.models.user import User, Domain
from candidate_service.common.models.misc import AreaOfInterest
from candidate_service.common.error_handling import InternalServerError
from candidate_service.common import talent_property_manager
from flask.ext.common.common.geo_services.geo_coordinates import get_geocoordinates_bounding

API_VERSION = "2013-01-01"
MYSQL_DATE_FORMAT = '%Y-%m-%dT%H:%i:%S.%fZ'
BATCH_REQUEST_LIMIT_BYTES = 5 * 1024 * 1024
DOCUMENT_SIZE_LIMIT_BYTES = 1024 * 1024
CLOUD_SEARCH_SDF_S3_FOLDER = "CloudSearchSDF"
CLOUD_SEARCH_MAX_LIMIT = 10000

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
    'talent_pools':                  dict(IndexFieldType='int-array',       IntArrayOptions={'ReturnEnabled': False}),
    'dumb_lists':                    dict(IndexFieldType='int-array',       IntArrayOptions={'ReturnEnabled': False}),
}

# Get all the credentials from environment variable
AWS_ACCESS_KEY_ID = talent_property_manager.get_aws_key()
AWS_SECRET_ACCESS_KEY = talent_property_manager.get_aws_secret()

CLOUD_SEARCH_REGION = talent_property_manager.get_cloudsearch_region()
CLOUD_SEARCH_DOMAIN_NAME = talent_property_manager.get_cloudsearch_domain_name()

filter_queries_list = []
search_queries_list = []
coordinates = []
geo_params = dict()


def get_cloud_search_connection():
    """
    Get cloud search connection
    :return:
    """
    global _cloud_search_connection_layer_2, _cloud_search_domain
    if not _cloud_search_connection_layer_2:
        _cloud_search_connection_layer_2 = boto.connect_cloudsearch2(aws_access_key_id=AWS_ACCESS_KEY_ID,
                                                                     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                                                     sign_request=True,
                                                                     region=CLOUD_SEARCH_REGION)

        _cloud_search_domain = _cloud_search_connection_layer_2.lookup(CLOUD_SEARCH_DOMAIN_NAME)
        if not _cloud_search_domain:
            _cloud_search_connection_layer_2.create_domain(CLOUD_SEARCH_DOMAIN_NAME)

    return _cloud_search_connection_layer_2

#
# def create_domain(domain_name=None):
#     """
#     Creates the given domain if doesn't exist
#
#     :param domain_name: the domain name. If none, uses the one from config
#     :return: Domain object, or None if not found
#     """
#     if not domain_name:
#         domain_name = CLOUD_SEARCH_DOMAIN_NAME
#     layer2 = get_cloud_search_connection()
#     if not layer2.lookup(domain_name):
#         return layer2.create_domain(domain_name)


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


def define_index_fields():
    """
    Add/Edit new index field form above defined index fields.
     * to delete index fields call delete_index_fields
    :return:
    """
    conn = get_cloud_search_connection()
    for index_field_name, index_field_options in INDEX_FIELD_NAME_TO_OPTIONS.iteritems():
        logger.info("Defining index field %s", index_field_name)
        index_field_dict = deepcopy(index_field_options)
        index_field_dict['IndexFieldName'] = index_field_name
        conn.layer1.define_index_field(_cloud_search_domain.name, index_field_dict)
        time.sleep(1)  # To prevent throttling


def delete_index_fields():
    """
    Deletes above defined index fields.
    :return:
    """
    if current_app.config['GT_ENVIRONMENT'] is not 'dev':
        raise Exception("Can't call delete_index_fields() in prod! Use the console instead")
    conn = get_cloud_search_connection()
    for index_field_name in INDEX_FIELD_NAME_TO_OPTIONS:
        logger.info("Deleting index field %s", index_field_name)
        conn.layer1.delete_index_field(_cloud_search_domain.name, index_field_name)


def index_documents():
    """
    Index all the documents
    :return:
    """
    conn = get_cloud_search_connection()
    conn.layer1.index_documents(_cloud_search_domain.name)


def _build_candidate_documents(candidate_ids):
    """
    Returns dicts like: {type="add", id="{candidate_id}", fields={dict of fields to values}}

    """
    if not candidate_ids:
        logger.warn("Attempted to build candidate documents when candidate_ids=%s", candidate_ids)
        return []
    group_concat_separator = '~~~'

    sql_query = """
    SELECT
                # Candidate table info
                candidate.id AS `id`, candidate.firstName AS `first_name`, candidate.lastName AS `last_name`,
                candidate.statusId AS `status_id`, DATE_FORMAT(candidate.addedTime, '%(date_format)s') AS `added_time`,
                candidate.ownerUserId AS `user_id`, candidate.objective AS `objective`,
                candidate.sourceId AS `source_id`, candidate.sourceProductId AS `source_product_id`,
                candidate.totalMonthsExperience AS `total_months_experience`,

                # Address & contact info
                candidate_address.city AS `city`, candidate_address.state AS `state`, candidate_address.zipCode AS `zip_code`,
                candidate_address.coordinates AS `coordinates`,
                GROUP_CONCAT(DISTINCT candidate_email.address SEPARATOR '%(sep)s') AS `email`,

                # Talent Pools
                GROUP_CONCAT(DISTINCT talent_pool_candidate.talent_pool_id SEPARATOR '%(sep)s') AS `talent_pools`,

                # Dumb Lists
                GROUP_CONCAT(DISTINCT smart_list_candidate.smartlistId SEPARATOR '%(sep)s') AS `dumb_lists`,

                # AOIs and Custom Fields
                GROUP_CONCAT(DISTINCT candidate_area_of_interest.areaOfInterestId SEPARATOR '%(sep)s') AS `area_of_interest_id`,
                GROUP_CONCAT(DISTINCT CONCAT(candidate_custom_field.customFieldId, '|', candidate_custom_field.value) SEPARATOR '%(sep)s') AS `custom_field_id_and_value`,

                # Military experience
                GROUP_CONCAT(DISTINCT candidate_military_service.highestGrade SEPARATOR '%(sep)s') AS `military_highest_grade`,
                GROUP_CONCAT(DISTINCT candidate_military_service.serviceStatus SEPARATOR '%(sep)s') AS `military_service_status`,
                GROUP_CONCAT(DISTINCT candidate_military_service.branch SEPARATOR '%(sep)s') AS `military_branch`,
                GROUP_CONCAT(DISTINCT DATE_FORMAT(candidate_military_service.toDate, '%(date_format)s') SEPARATOR '%(sep)s') AS `military_end_date`,

                # Experience
                GROUP_CONCAT(DISTINCT candidate_experience.organization SEPARATOR '%(sep)s') AS `organization`,
                GROUP_CONCAT(DISTINCT candidate_experience.position SEPARATOR '%(sep)s') AS `position`,
                GROUP_CONCAT(DISTINCT candidate_experience_bullet.description SEPARATOR '%(sep)s') AS `experience_description`,

                # Education
                GROUP_CONCAT(DISTINCT candidate_education.schoolName SEPARATOR '%(sep)s') AS `school_name`,
                GROUP_CONCAT(DISTINCT candidate_education_degree.degreeType SEPARATOR '%(sep)s') AS `degree_type`,
                GROUP_CONCAT(DISTINCT candidate_education_degree.degreeTitle SEPARATOR '%(sep)s') AS `degree_title`,
                GROUP_CONCAT(DISTINCT DATE_FORMAT(candidate_education_degree.endTime, '%(date_format)s') SEPARATOR '%(sep)s') AS `degree_end_date`,
                GROUP_CONCAT(DISTINCT candidate_education_degree_bullet.concentrationType SEPARATOR '%(sep)s') AS `concentration_type`,

                # Skill & unidentified
                GROUP_CONCAT(DISTINCT candidate_skill.description SEPARATOR '%(sep)s') AS `skill_description`,
                GROUP_CONCAT(DISTINCT candidate_unidentified.description SEPARATOR '%(sep)s') AS `unidentified_description`,

                # Rating and comments
                GROUP_CONCAT(DISTINCT CONCAT(candidate_rating.ratingTagId, '|', candidate_rating.value) SEPARATOR '%(sep)s') AS `candidate_rating_id_and_value`,
                GROUP_CONCAT(DISTINCT candidate_text_comment.comment SEPARATOR '%(sep)s') AS `text_comment`

    FROM        candidate

    LEFT JOIN   talent_pool_candidate ON (candidate.id = talent_pool_candidate.candidate_id)
    LEFT JOIN   smart_list_candidate ON (candidate.id = smart_list_candidate.candidateId)
    LEFT JOIN   candidate_address ON (candidate.id = candidate_address.candidateId)
    LEFT JOIN   candidate_email ON (candidate.id = candidate_email.candidateId)

    LEFT JOIN   candidate_area_of_interest ON (candidate.id = candidate_area_of_interest.candidateId)
    LEFT JOIN   candidate_custom_field ON (candidate.id = candidate_custom_field.candidateId)

    LEFT JOIN   candidate_military_service ON (candidate.id = candidate_military_service.candidateId)

    LEFT JOIN   candidate_experience ON (candidate.id = candidate_experience.candidateId)
    LEFT JOIN   candidate_experience_bullet ON (candidate_experience.id =
    candidate_experience_bullet.candidateExperienceId)

    LEFT JOIN   candidate_education ON (candidate.id = candidate_education.candidateId)
    LEFT JOIN   candidate_education_degree ON (candidate_education.id = candidate_education_degree.candidateEducationId)
    LEFT JOIN   candidate_education_degree_bullet ON (candidate_education_degree.id = candidate_education_degree_bullet.
    candidateEducationDegreeId)

    LEFT JOIN   candidate_skill ON (candidate.id = candidate_skill.candidateId)
    LEFT JOIN   candidate_unidentified ON (candidate.id = candidate_unidentified.candidateId)

    LEFT JOIN   candidate_rating ON (candidate.id = candidate_rating.candidateId)
    LEFT JOIN   candidate_text_comment ON (candidate.id = candidate_text_comment.candidateId)

    WHERE       candidate.id IN (%(candidate_ids_string)s)

    GROUP BY    candidate.id
    ;
    """ % dict(candidate_ids_string=','.join(["%s" % candidate_id for candidate_id in candidate_ids]),
               sep=group_concat_separator,
               date_format=MYSQL_DATE_FORMAT)

    results = db.session.execute(sql_query)

    # Go through results & build action dicts
    action_dicts = []
    for field_name_to_sql_value in results:
        candidate_id = field_name_to_sql_value['id']
        action_dict = dict(type='add', id=str(candidate_id))

        # Remove keys with empty values
        field_name_to_sql_value = {k: v for k, v in field_name_to_sql_value.items() if v}

        # Massage 'field_name_to_sql_value' values into the types they are supposed to be
        for field_name in field_name_to_sql_value.keys():
            index_field_options = INDEX_FIELD_NAME_TO_OPTIONS.get(field_name)

            if not index_field_options:
                logger.error("Unknown field name, could not build document: %s", field_name)
                continue

            sql_value = field_name_to_sql_value[field_name]
            if not sql_value:
                continue

            index_field_type = index_field_options['IndexFieldType']
            if 'array' in index_field_type:
                sql_value_array = sql_value.split(group_concat_separator)
                if index_field_type == 'int-array':
                    # If int-array, turn all values to ints
                    sql_value_array = [int(field_value) for field_value in sql_value_array]
                field_name_to_sql_value[field_name] = sql_value_array

        # Add the required values we didn't get from DB
        field_name_to_sql_value_row = User.query.filter_by(
            id=field_name_to_sql_value['user_id']).first()
        field_name_to_sql_value['domain_id'] = field_name_to_sql_value_row.domain_id
        action_dict['fields'] = field_name_to_sql_value
        action_dicts.append(action_dict)

    return action_dicts


def upload_candidate_documents(candidate_ids):
    """
    Upload all the candidate documents to cloud search
    :param candidate_ids: id of candidates for documents to be uploaded
    :return:
    """
    if isinstance(candidate_ids, int) or isinstance(candidate_ids, long):
        candidate_ids = [candidate_ids]
    logger.info("Uploading %s candidate documents. Generating action dicts...", len(candidate_ids))
    start_time = time.time()
    action_dicts = _build_candidate_documents(candidate_ids)
    logger.info("Action dicts generated (took %ss). Sending %s action dicts", time.time() - start_time,
                len(action_dicts))
    adds, deletes = _send_batch_request(action_dicts)
    if deletes:
        logger.error("Shouldn't have gotten any deletes in a batch add operation.Got %s deletes.candidate_ids: %s",
                     deletes, candidate_ids)
    return adds


def upload_candidate_documents_in_domain(domain_id):
    """
    Upload all the candidates from given domain to cloudsearch
    :param domain_id: Domain id of which all the candidates needs to be uploaded to cloudsearch
    :return: count of total uploaded candidates
    """

    candidates = Candidate.query.with_entities(Candidate.id).join(User).filter(Candidate.user_id == User.id,
                                                                               User.domain_id == domain_id).all()
    candidate_ids = [candidate.id for candidate in candidates]
    logger.info("Uploading %s candidates of domain id %s", len(candidate_ids), domain_id)
    return upload_candidate_documents(candidate_ids)


def upload_candidate_documents_of_user(user_id):
    """
    Upload all candidates belonging to given user
    :param user_id: Id of user whose candidates needs to be uploaded
    :return: count of total uploaded candidates
    """
    candidates = Candidate.query.with_entities(Candidate.id).filter_by(user_id=user_id).all()
    candidate_ids = [candidate.id for candidate in candidates]
    logger.info("Uploading %s candidates of user (user id = %s)", len(candidate_ids), user_id)
    return upload_candidate_documents(candidate_ids=candidate_ids)


def upload_all_candidate_documents():
    """
    Upload all the candidates present in system to cloudsearch.
    :return: total number of candidates uploaded
    """
    adds = 0
    domains = Domain.query.with_entities(Domain.id).all()
    for domain in domains:
        logger.info("Uploading all candidates of domain %s", domain.id)
        adds += upload_candidate_documents_in_domain(domain.id)
    return adds


def delete_candidate_documents(candidate_ids):
    """Delete specified candidate's documents from cloudsearch"""
    if isinstance(candidate_ids, int):
        candidate_ids = [candidate_ids]
    action_dicts = [dict(type='delete', id=candidate_id) for candidate_id in candidate_ids]
    adds, deletes = _send_batch_request(action_dicts)
    if adds:
        logger.error("Shouldn't have gotten any adds in a batch delete operation.Got %s adds.candidate_ids: %s", adds,
                     candidate_ids)
    return deletes


def delete_all_candidate_documents():
    """
    Should only be used for dev domains, if all candidate documents needs to be deleted from CloudSearch.
    It only works on dev domain (to avoid the function hitting accidentally on production)

    """
    if current_app.config('GT_ENVIRONMENT') is not 'dev':
        raise Exception("Can't call delete_all_candidate_documents() in prod! Use the console instead")

    # Get all candidate ids by searching for everything except a nonsense string
    params = {'ret': "_no_fields", 'query': "-12421412421412iowejdsklxc", 'query_parser': 'lucene', "cursor": "initial",
              "size": 5000}

    search_service = _cloud_search_domain_connection()
    no_more_candidates = False
    total_num_deleted = 0
    while not no_more_candidates:
        # Get the next batch of candidates to delete
        results = search_service.search(**params)
        matches = results['hits']['hit']
        candidate_ids_to_delete = [item['id'] for item in matches]

        # Now delete them
        logger.debug("delete_all_candidate_documents: Deleting %s candidate documents",
                     len(candidate_ids_to_delete))
        num_deleted = delete_candidate_documents(candidate_ids_to_delete)
        if not num_deleted:
            no_more_candidates = True

        # Update cursor for next run
        new_cursor = results['hits']['cursor']
        params['cursor'] = new_cursor

        total_num_deleted += num_deleted
    return total_num_deleted


def _send_batch_request(action_dicts):
    adds, deletes = 0, 0
    get_cloud_search_connection()
    import boto.cloudsearch2.document
    document_service_connection = boto.cloudsearch2.document.DocumentServiceConnection(domain=_cloud_search_domain)
    max_possible_request_size_bytes = 2  # Opening/closing brackets

    # If the batch request size > 5MB, split it up
    for i, action_dict in enumerate(action_dicts):
        action_dict_json = simplejson.dumps(action_dict)
        if len(action_dict_json) > DOCUMENT_SIZE_LIMIT_BYTES:
            # Individual doc size shouldn't exceed 1MB
            logger.error("_send_batch_request: action dict was > 1MB, so couldn't send: %s" % action_dict)
            continue
        elif max_possible_request_size_bytes < BATCH_REQUEST_LIMIT_BYTES:
            # Add doc to aggregated string if it fits
            if action_dict['type'] == 'delete':
                document_service_connection.delete(action_dict['id'])
                max_possible_request_size_bytes += 30  # approx. delete dict size
            else:
                document_service_connection.add(action_dict['id'], fields=action_dict['fields'])
                max_possible_request_size_bytes += 40 + len(action_dict_json)  # approx. add dict size

        if (len(action_dicts) == i + 1) or \
                (max_possible_request_size_bytes + DOCUMENT_SIZE_LIMIT_BYTES > BATCH_REQUEST_LIMIT_BYTES):
            """
            If we're at the end of the loop, or once 4MB is reached, send out the request.
            We sent it out at 4MB (not 5MB) because the last
            document in the batch could be 1MB.
            """
            try:
                result = document_service_connection.commit()
            except Exception:
                logger.exception("_send_batch_request: Exception when sending batch request")
                result = None
            document_service_connection.clear_sdf()
            max_possible_request_size_bytes = 2
            if result:
                if result.errors:
                    logger.error("Received errors committing action_dicts to CloudSearch: %s", result.errors)
                adds += result.adds
                deletes += result.deletes

    return adds, deletes


def _cloud_search_domain_connection():
    get_cloud_search_connection()
    return _cloud_search_domain.get_search_service().domain_connection


def search_candidates(domain_id, request_vars, search_limit=15, count_only=False):
    """
    Searches candidates based on domain_id and search_filters provided.
    Search Engine: Amazon Cloud Search

    :param domain_id: Search candidates in given domain Id
    :param request_vars: Search criteria, or various search filters
    :param search_limit: Defaults to 15.
    :return: Search results in format described on `search service` apiary document.

    Set search_limit = 0 for no limit, candidate_ids_only returns dict of candidate_ids.
    Parameters in 'request_vars' could be single values or arrays.
    """
    # Clear all queries and filters list for fresh search
    _clear_filter_queries_and_search_queries_list()

    if request_vars:
        for var_name in request_vars.keys():
            if "[]" == var_name[-2:]:
                request_vars[var_name[:-2]] = request_vars[var_name]
        get_filter_query_from_request_vars(request_vars)

    # Search all candidates under domain
    filter_queries_list.append(["(term field=domain_id %s)" % domain_id])

    dumb_list_query_string, dumb_list_filter_query_string = '', ''
    # This parameter is for internal Talent-Pipeline search only
    if isinstance(request_vars.get('dumb_list_ids'), list):
        dumb_list_query_string = " OR ".join("dumb_lists:%s" % dumb_list_id for dumb_list_id in
                                             request_vars.get('dumb_list_ids'))
        dumb_list_filter_query_string = "(or %s)" % ' '.join("dumb_lists:%s" % dumb_list_id for dumb_list_id in
                                                             request_vars.get('dumb_list_ids'))
    elif request_vars.get('dumb_list_ids'):
        dumb_list_filter_query_string = dumb_list_query_string = "dumb_lists:%s" % request_vars.get('dumb_list_ids')

    # Sorting
    sort = '%s %s'
    if request_vars.get('sort_by'):
        sort_field, sort_order = request_vars.get('sort_by')
    else:
        sort_field, sort_order = (DEFAULT_SORT_FIELD, DEFAULT_SORT_ORDER)

    if sort_field == 'distance' and not coordinates:
        # if coordinates not found set sorting to default.
        sort_field = DEFAULT_SORT_FIELD
        sort_order = DEFAULT_SORT_ORDER

    sort = sort % (sort_field, sort_order.lower())

    page = int(request_vars.get('page')) if (request_vars.get('page') and (int(request_vars.get('page')) > 0)) else 1
    offset = (page - 1) * search_limit if search_limit else 0

    if count_only:
        search_limit = 0
        offset = 0
    elif search_limit == 0 or search_limit > CLOUD_SEARCH_MAX_LIMIT:
        search_limit = CLOUD_SEARCH_MAX_LIMIT

    if not search_queries_list:
        # If no search query is provided, (may be in case of landing talent page) then fetch all results
        query_string = "id:%s" % request_vars['id'] if request_vars.get('id') else "*:*"

    else:
        query_string = " AND ".join(search_queries_list) if len(search_queries_list) > 1 \
            else " ".join(search_queries_list)
        if request_vars.get('id'):
            # If we want to check if a certain candidate ID is in a smartlist
            query_string = "id:%s AND %s" % (request_vars['id'], query_string)
        # For TalentPipeline candidate search we'll need to query candidates of given dumb_lists
        if dumb_list_query_string:
            query_string = "((%s) OR (%s))" % (dumb_list_query_string, query_string)

    params = dict(query=query_string, sort=sort, start=offset, size=search_limit)
    params['query_parser'] = 'lucene'

    filter_query_strings = []
    for filter_query in filter_queries_list:
        if filter_query:
            filter_query_strings.append("(and %s)" % ' '.join(filter_query) if len(filter_query) > 1
                                        else ' '.join(filter_query))

    params['filter_query'] = "(and %s)" % " ".join(filter_query_strings) if len(filter_query_strings) > 1 \
        else ' '.join(filter_query_strings)

    if dumb_list_query_string:
        if len(filter_query_strings) > 1:
            params['filter_query'] = "(or %s %s)" % (dumb_list_filter_query_string, params['filter_query'])
        else:
            # Length of filter_query_strings is 1 because there would be domain_id term at least
            params['filter_query'] = dumb_list_filter_query_string

    # Add talent_pool_id in filter_queries
    if request_vars.get('talent_pool_id'):
        params['filter_query'] = "(and %s (term field=talent_pools  %s))" % (params['filter_query'],
                                                                             request_vars.get('talent_pool_id'))

    if sort_field == "distance":
        params['expr'] = "{'distance':'haversin(%s,%s,coordinates.latitude,coordinates.longitude)'}"\
                         % (coordinates[0], coordinates[1])
        params['sort'] = "distance %s" % sort_order

    # Adding facet fields parameters

    if not count_only:
        params['facet'] = "{area_of_interest_id:{size:500},source_id:{size:50}," \
                          "user_id:{size:50},status_id:{size:50},skill_description:{size:500}," \
                          "position:{size:50},school_name:{size:500},degree_type:{size:50}," \
                          "concentration_type:{size:50},military_service_status:{size:50}," \
                          "military_branch:{size:50},military_highest_grade:{size:50}," \
                          "custom_field_id_and_value:{size:1000}}"

    if geo_params:
        params = dict(params.items() + geo_params.items())

    # Return data dictionary. Initializing here, to have standard return type across the function
    search_results = dict(total_found=0,
                          total_count=0,
                          candidates=[],
                          max_score=0,
                          max_pages=0,
                          facets={})

    # Looks like cloud_search does not have something like return only count predefined
    # removing fields and returned content should speed up network request
    if 'count_only' in request_vars:
        params['ret'] = "_no_fields,_score"
        params['size'] = 0
    elif request_vars.get('fields'):
        params['ret'] = request_vars['fields']
    else:
        params['ret'] = "_all_fields,_score"

    # Max cloud_search search limit, then implement cursor (paging beyond 10000 limit)
    if search_limit >= CLOUD_SEARCH_MAX_LIMIT:
        candidate_ids, total_found, error = _cloud_search_fetch_all(params)
        if error:
            return search_results
        return dict(total_found=total_found, candidate_ids=candidate_ids)

    # Make search request with error handling

    search_service = _cloud_search_domain_connection()

    try:
        results = search_service.search(**params)
    except Exception as ex:
        logger.exception("Exception occurred while searching candidates from cloudsearch. "
                         "Search params: %s. Exception: %s" % (params, ex))
        return InternalServerError("SearchServiceError: Error while searching the candidates.")

    matches = results['hits']['hit']

    total_found = results['hits']['found']

    if count_only:
        return dict(total_found=total_found, candidate_ids=[])

    facets = get_faceting_information(results.get('facets'))

    # Update facets
    queries_list = [query for filter_query_list in filter_queries_list for query in filter_query_list]
    _update_facet_counts(queries_list, params['filter_query'], facets, query_string, domain_id)

    # for facet_field_name, facet_dict in facets.iteritems():
    #     facets[facet_field_name] = sorted(facet_dict.iteritems(), key=operator.itemgetter(1), reverse=True)
    if facets.get('custom_field_id_and_value', dict()):
        _kaiser_custom_fields_facets(request_vars, facets)

    # Get max score
    max_score = _get_max_score(params, search_service)

    max_pages = int(math.ceil(total_found / float(search_limit))) if search_limit else 1
    fields_data = [data['fields'] for data in matches]
    search_results['total_found'] = total_found
    search_results['candidates'] = fields_data
    search_results['max_score'] = max_score
    search_results['max_pages'] = max_pages
    search_results['facets'] = facets
    # for values in search_results['candidates']:
    #     if 'email' in values:
    #         values['email'] = {"address": values['email']}
    # Returns a dictionary with all the candidates data
    return search_results


# Get the facet information from database with given ids
def get_faceting_information(facets):
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
        search_facets_values['username'] = get_username_facet_info_with_ids(facet_owner)

    if facet_aoi:
        search_facets_values['area_of_interest'] = get_facet_info_with_ids(AreaOfInterest, facet_aoi,
                                                                                'name')

    if facet_source:
        search_facets_values['source'] = get_facet_info_with_ids(CandidateSource, facet_source,
                                                                      'description')

    if facet_status:
        search_facets_values['status'] = get_facet_info_with_ids(CandidateStatus, facet_status,
                                                                      'description')

    if facet_skills:
        search_facets_values['skills'] = get_bucket_facet_value_count(facet_skills)

    if facet_position:
        search_facets_values['position'] = get_bucket_facet_value_count(facet_position)

    if facet_university:
        search_facets_values['school_name'] = get_bucket_facet_value_count(facet_university)

    if facet_degree_type:
        search_facets_values['degree_type'] = get_bucket_facet_value_count(facet_degree_type)

    if facet_major:
        search_facets_values['concentration_type'] = get_bucket_facet_value_count(facet_major)

    if facet_military_service_status:
        search_facets_values['military_service_status'] = get_bucket_facet_value_count(facet_military_service_status)

    if facet_military_branch:
        search_facets_values['military_branch'] = get_bucket_facet_value_count(facet_military_branch)

    if facet_military_highest_grade:
        search_facets_values['military_highest_grade'] = get_bucket_facet_value_count(facet_military_highest_grade)

    # TODO: productFacet, customFieldKP facets are remaining, how to do it?
    if facet_custom_field_id_and_value:
        search_facets_values['custom_field_id_and_value'] = get_bucket_facet_value_count(facet_custom_field_id_and_value)

    return search_facets_values


def get_username_facet_info_with_ids(facet_owner):
    tmp_dict = get_facet_info_with_ids(User, facet_owner, 'email')
    # Dict is (email, value) -> count
    username_facets = []
    # Replace each user's email with name
    for username_facet in tmp_dict:
        new_tmp_dict = {}
        user_row = User.query.filter_by(email=username_facet['value']).first()
        new_tmp_dict['id'] = username_facet['id']
        new_tmp_dict['value'] = user_row.first_name+" "+user_row.last_name
        new_tmp_dict['count'] = username_facet['count']
        username_facets.append(new_tmp_dict)
    return username_facets


def get_facet_info_with_ids(table_name, facet, field_name):
    """
    Few facets are filtering using ids, for those facets with ids, get their names (from db) for displaying on html
    also send ids so as to ease search with filter queries,
    returned ids will serve as values to checkboxes.
    :param facet: Facet as received from cloudsearch (bucket value contains id of facet)
    :param field_name: Name which is to be returned for UI. This is name of field from table
    :return: Dictionary with field name as key and count of candidates + facet id as value
    """

    facets_list = []
    for bucket in facet:
        tmp_dict = {}
        row = table_name.query.filter_by(id=int(bucket['value'])).first()
        if row:
            tmp_dict['id'] = bucket['value']
            tmp_dict['value'] = getattr(row, field_name)
            tmp_dict['count'] = bucket['count']
            facets_list.append(tmp_dict)
    return facets_list


def get_bucket_facet_value_count(facet):
    """
    This function is specifically for those facets which are having proper values not ids(which need database query)
    Collects list of dictionaries having value and count and return single dictionary with value, count pair
    :param facet: (type-List of dicts): single facet of facets returned from cloud_search (contains count & value dicts)
    eg: {u'buckets': [{u'count': 5, u'value': u'Bachelors'}, {u'count': 3, u'value': u'Masters'}]}
    :return: dictionary with value as key and count as value
    eg: {'Bachelors':5, 'Masters':3}
    """
    facet_bucket = []
    for bucket in facet:
        tmp_dict = dict()
        tmp_dict["value"] = bucket['value']
        tmp_dict["count"] = bucket['count']
        facet_bucket.append(tmp_dict)
    return facet_bucket


def _update_facet_counts(filter_queries, params_fq, existing_facets, query_string, domain_id):
    """
    For multi-select facets, return facet count and values based on filter queries
    :param filter_queries:
    :return:
    """
    search_service = _cloud_search_domain_connection()
    # Multi-select facet scenario
    for filter_query in filter_queries:
        if 'user_id' in filter_query:
            fq_without_user_id = params_fq.replace(filter_query, '')
            query_user_id_facet = {'query': query_string, 'size': 0, 'filter_query': fq_without_user_id,
                                   'query_parser': 'lucene', 'ret': '_no_fields', 'facet': "{user_id: {size:50}}"}
            result_user_id_facet = search_service.search(**query_user_id_facet)
            facet_owner = result_user_id_facet['facets']['user_id']['buckets']
            existing_facets['username'] = get_username_facet_info_with_ids(facet_owner)
        if 'area_of_interest_id' in filter_query:
            fq_without_area_of_interest = params_fq.replace(filter_query, '')
            query_area_of_interest_facet = {'query': query_string, 'size': 0,
                                            'filter_query': fq_without_area_of_interest, 'query_parser': 'lucene',
                                            'ret': '_no_fields', 'facet': "{area_of_interest_id: {size:500}}"}
            result_area_of_interest_facet = search_service.search(**query_area_of_interest_facet)
            facet_aoi = result_area_of_interest_facet['facets']['area_of_interest_id']['buckets']
            existing_facets['area_of_interest'] = get_facet_info_with_ids(AreaOfInterest, facet_aoi,
                                                                               'name')
        if 'source_id' in filter_query:
            fq_without_source_id = params_fq.replace(filter_query, '')
            query_source_id_facet = {'query': query_string, 'size': 0, 'filter_query': fq_without_source_id,
                                     'query_parser': 'lucene', 'ret': '_no_fields', 'facet': "{source_id: {size:50}}"}
            result_source_id_facet = search_service.search(**query_source_id_facet)
            facet_source = result_source_id_facet['facets']['source_id']['buckets']
            existing_facets['source'] = get_facet_info_with_ids(CandidateSource, facet_source, 'description')
        if 'school_name' in filter_query:
            fq_without_school_name = params_fq.replace(filter_query, '')
            query_school_name_facet = {'query': query_string, 'size':0, 'filter_query': fq_without_school_name,
                                       'query_parser': 'lucene', 'ret': '_no_fields',
                                       'facet': "{school_name: {size:500}}"}
            result_school_name_facet = search_service.search(**query_school_name_facet)
            facet_school = result_school_name_facet['facets']['school_name']['buckets']
            existing_facets['school_name'] = get_bucket_facet_value_count(facet_school)
        if 'degree_type' in filter_query:
            fq_without_degree_type = params_fq.replace(filter_query, '')
            query_degree_type_facet = {'query': query_string, 'size': 0, 'filter_query': fq_without_degree_type,
                                       'query_parser': 'lucene', 'ret': '_no_fields', 'facet':
                                           "{degree_type: {size:50}}"}
            result_degree_type_facet = search_service.search(**query_degree_type_facet)
            facet_degree_type = result_degree_type_facet['facets']['degree_type']['buckets']
            existing_facets['degree_type'] = get_bucket_facet_value_count(facet_degree_type)


def _cloud_search_fetch_all(params):
    """ Fetches all candidates from cloudsearch using cursor i.e. when search is more than 10000 candidates
    :param params: search params
    :return: candidate_ids:all candidate ids,
    :return: total_found: total number of candidate found
    :return: error: if there was error while executing search query
    """
    search_service = _cloud_search_domain_connection()
    params['cursor'] = 'initial'  # Initialize cursor
    # remove start, as it is produces error with cursor
    del params['start']
    no_more_candidates = False
    total_found = 0
    candidate_ids = []
    error = False
    # If size is more than 10000, cloud_search will give error, so set size to chunk of 10000 candidates and fetch all
    if params['size'] > CLOUD_SEARCH_MAX_LIMIT:
        params['size'] = CLOUD_SEARCH_MAX_LIMIT
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


def _get_source_id(request_vars):
    """
    Get source id of candidates
    :param request_vars:
    :return:
    """

    if isinstance(request_vars['source_id'], basestring):  # source_id is string
        if 'product_' in request_vars['source_id']:
            request_vars['product_id'] = request_vars['source_id'].replace('product_', '')
            request_vars['source_id'] = ''
    else:  # source_id is array
        new_source_ids = []
        for source_or_product in request_vars['source_id']:
            if 'product_' in source_or_product:  # if product id found, add to product_id array

                if not request_vars['product_id']:
                    request_vars['product_id'] = []

                request_vars['product_id'].append(source_or_product.replace('product_', ''))
            else:  # otherwise, add to new product ids array
                new_source_ids.append(source_or_product)
        request_vars['source_id'] = new_source_ids
    return request_vars['source_id']


def _get_search_queries(request_vars):
    """
    Get the fiter query
    :param request_vars:
    :return:
    """
    # If query is array, separate values by spaces
    query = request_vars.get('query')
    if query and not isinstance(query, basestring):
        q = ' '.join(query)
        search_queries_list.append(q)
    elif query:
        search_queries_list.append(query)

    return search_queries_list


def _search_with_location(location, radius):
    """
    :param request_vars:
    :param location:
    :return:
    """
    filter_queries = []

    # If zipcode and radius provided, get coordinates & do a geo search
    is_zipcode = re.match(r"^\d+$", location) is not None
    # Convert miles to kilometers, required by geo_location calculator
    # if no radius is given set default distance to 80.47 (50 miles)
    distance_in_km = float(radius)/0.62137 if radius else 80.47
    coords_dict = get_geocoordinates_bounding(location, distance_in_km)
    if coords_dict and coords_dict.get('point'):
        if coords_dict['point']:
            # If coordinates found, then only perform location search
            filter_queries.append("coordinates:['%s,%s','%s,%s']" % (coords_dict['top_left'][0],
                                                                     coords_dict['top_left'][1],
                                                                     coords_dict['bottom_right'][0],
                                                                     coords_dict['bottom_right'][1]))
    elif is_zipcode:

        """If coodinates were not found with given location and if location is type of zipcode,
        then search based on zipcode"""

        filter_queries.append("(term field=zip_code '%s')" % location)

    coordinates.extend(list(coords_dict['point']))

    return filter_queries


def _get_candidates_by_filter_date(request_vars):
    """
    Get the candidates data with given filtered date
    :param request_vars:
    :return:
    """
    filter_queries = []
    add_time_from = request_vars.get('date_from')
    add_time_to = request_vars.get('date_to')

    if add_time_from or add_time_to:
        add_time_from = "['%s'" % add_time_from if add_time_from else "{"  # following cloudsearch syntax
        add_time_to = "'%s']" % add_time_to if add_time_to else "}"
        filter_queries.append("(range field=added_time %s,%s)" % (add_time_from, add_time_to))

    return filter_queries


def _search_custom_fields(request_vars):
    """

    :param request_vars:
    :return:
    """
    filter_queries = []
    # Handling custom fields
    custom_field_vars = list()
    city_of_interest_custom_fields = []
    for key, value in request_vars.items():
        if 'cf-' in key:
            cf_id = key.split('-')[1]

            # This is for handling kaiser's NUID custom field
            if int(cf_id) == 15 and value == 'Has NUID':
                cf_value = cf_id+'|'
                filter_queries.append("(prefix field=custom_field_id_and_value '%s')" % cf_value)
                continue

            # This is for handling standard custom values (not for email preferences)
            if type(value) == list:
                # To avoid REQUEST TOO LONG error we are limiting the search to 50 items
                # TODO: When Kaiser city of interest and state of interest is merged,remove the logic to truncate to 50.
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
        city_of_interest_custom_fields_index = [i for i, x in enumerate(custom_field_vars) if
                                                re.findall(r'\"38\|(.*?)\"', x)]

        if len(city_of_interest_custom_fields_index):
            for i in sorted(city_of_interest_custom_fields_index, reverse=True):
                city_of_interest_custom_fields.append(custom_field_vars[i])
                del custom_field_vars[i]

        if len(custom_field_vars):
            custom_fields_facets = ["custom_field_id_and_value:%s" % custom_field_facet for custom_field_facet in
                                    custom_field_vars]
            filter_queries.append("(or %s)" % " ".join(custom_fields_facets))
        if len(city_of_interest_custom_fields):
            city_of_interest_custom_fields_facets = ["custom_field_id_and_value:%s" %
                                                     city_of_interest_custom_fields_facet for
                                                     city_of_interest_custom_fields_facet in
                                                     city_of_interest_custom_fields]
            filter_queries.append("(or %s)" % " " . join(city_of_interest_custom_fields_facets))

    return filter_queries


def _kaiser_custom_fields_facets(request_vars, facets):

    # Special flag for kaiser's NUID custom field
    has_kaiser_nuid = False
    num_kaiser_nuids = 0
    custom_fields = dict()
    if facets.get('custom_field_id_and_value', dict()):
        for cf_facet in facets['custom_field_id_and_value']:
            # cf_hash example: 9|Top Gun
            # 9 = id of custom field (in this case, Movies)
            # right side of | is the value of that custom field
            cf_hash = cf_facet['value']
            cf_id = cf_hash.split('|')[0]
            cf_value = cf_hash.split('|')[1]
            cf_facet_count = cf_facet['count']

            """
            If the cf_id is 15 (NUID's for Kaiser),
                Do not add values to the custom_fields list,
                they just want facets for whether the candidate has a NUID or not

                Since cf_id 15 is requested as a facet, we'll handle it as a special case:
                facet.query={!ex=dt key="has NUID"}customFieldKP:15|*
            """
            if cf_id:
                has_kaiser_nuid = True
                num_kaiser_nuids += cf_facet_count
                continue

            if not custom_fields.get('cf-%d' % cf_id):
                custom_fields['cf-%d' % cf_id] = list()

            custom_fields['cf-%d' % cf_id].append({'value': cf_value, 'count': cf_facet_count})

        if has_kaiser_nuid:
            custom_fields['cf-15'] = [{'value': 'Has NUID', 'count': num_kaiser_nuids}]

        facets = dict(facets.items() + custom_fields.items())

    return facets


def _get_max_score(params, search_service):
    """
    Get maximum relevance score from cloudsearch with _score sorting and first result will contain the max_score.
    For performance optimization, this function is using size 1 and only _score will be returned
    :param params: same search_params as of the actual query
    :param search_service: cloudsearch search_service object.
    :return: Max relevance score
    """
    default_sorting = "%s %s" % (DEFAULT_SORT_FIELD, DEFAULT_SORT_ORDER)
    params['sort'] = default_sorting
    # Update the sort parameter, to have sorting based on _score, desc
    # Limit search to one result, we only want max_score which is top most row when sorted with above criteria
    params['size'] = 1
    params['ret'] = "_score"
    params['start'] = 0
    params.pop("facet", None)
    single_result = search_service.search(**params)
    single_hit = single_result['hits']['hit']
    if len(single_hit) > 0:
        max_score = single_hit[0]['fields']['_score']
    else:
        max_score = 1
    return max_score


def _get_candidates_fields_with_given_filters(fields_data):
    """
    Get only the filtered candidate fields
    :param fields_data:
    :return: search result with candidates filtered fields
    """
    # Checks the fields is is there in the search filter
    requested_data = request.args.get('fields').split(',')
    required_search_result = {}
    response_candidates_data = []
    for fields in fields_data:
        required_data = {fk: fields[fk] for fk in requested_data if fk in fields}
        response_candidates_data.append(required_data)

    required_search_result['candidates'] = response_candidates_data
    for values in required_search_result['candidates']:
        if 'email' in values:
            values['email'] = {"address": values['email']}
    if required_search_result:
        # Returns the filtered search data
        return required_search_result


def get_filter_query_from_request_vars(request_vars):
    """
    Get the filter query from requested filters
    :param request_vars:
    :return: filter_query
    """

    filter_queries = []

    # If source_id has product_id in it, then remove it and add product_id to filter request_vars
    if not request_vars.get('product_id') and request_vars.get('source_ids'):
        _get_source_id(request_vars)

    if request_vars.get('query'):
        _get_search_queries(request_vars)

    if request_vars.get('location'):
        location = request_vars.get('location')
        radius = request_vars.get('radius')
        filter_queries = filter_queries + _search_with_location(location, radius)
    if isinstance(request_vars.get('user_ids'), list):
        filter_queries.append("(or %s)" % ' '.join("user_id:%s" % uid for uid in request_vars.get('user_ids')))
    elif request_vars.get('user_ids'):
        filter_queries.append("(term field=user_id %s)" % request_vars.get('user_ids'))

    # TODO: Add areaOfInterestNameFacet logic here, we need this for legacy data on production

    if isinstance(request_vars.get('area_of_interest_ids'), list):
        filter_queries.append("(or %s)" % " ".join("area_of_interest_id:%s" % aoi for aoi in
                                                   request_vars.get('area_of_interest_ids')))
    elif request_vars.get('area_of_interest_ids'):
        filter_queries.append("(term field=area_of_interest_id  %s)" % request_vars.get('area_of_interest_ids'))

    if isinstance(request_vars.get('status_ids'), list):
        filter_queries.append("(or %s)" % " ".join("status_id:%s" % status_facet for status_facet in
                                                   request_vars.get('status_ids')))
    elif request_vars.get('status_ids'):
        filter_queries.append("(term field=status_id %s)" % request_vars.get('status_ids'))

    if isinstance(request_vars.get('source_ids'), list):
        # search for exact values in facets
        source_facets = [ "source_id:%s" % source_facet for source_facet in request_vars.get('source_ids')]
        filter_queries.append("(or %s)" % ' '.join(source_facets))
    elif request_vars.get('source_ids'):
        filter_queries.append("(term field=source_id %s)" % request_vars.get('source_ids'))

    # Set filter range for years experience, if given
    if request_vars.get('minimum_years_experience') or request_vars.get('maximum_years_experience'):
        # set default to 0 because * doesn't works with cloudsearch
        min_months = int(request_vars.get('minimum_years_experience')) * 12 if \
            request_vars.get('minimum_years_experience') else 0
        # set default to 480 (max for 40 years)
        max_months = int(request_vars.get('maximum_years_experience')) * 12 if \
            request_vars.get('maximum_years_experience') else 480
        filter_queries.append("(range field=total_months_experience [%s,%s])" % (min_months, max_months))

    # date filtering
    if request_vars.get('date_from' or 'date_to'):
        filter_queries = filter_queries + _get_candidates_by_filter_date(request_vars)

    if isinstance(request_vars.get('job_title'), list):
        # search for exact values in facets
        position_facets = ["position:'%s'" % position_facet for position_facet in request_vars.get('job_title')]
        filter_queries.append("(and %s)" % " ".join(position_facets))
    elif request_vars.get('job_title'):
        filter_queries.append("( term field=position '%s')" % request_vars.get('job_title'))

    if isinstance(request_vars.get('skills'), list):
        # search for exact values in facets
        skill_facets = ["skill_description:'%s'" % skill_facet for skill_facet in
                        request_vars.get('skills')]
        filter_queries.append("(and %s )" % " ".join(skill_facets))
    elif request_vars.get('skills'):
        filter_queries.append("(term field=skill_description '%s')" % request_vars.get('skills'))

    if isinstance(request_vars.get('degree_type'), list):
        # search for exact values in facets
        degree_facets = ["degree_type:'%s'" % degree_facet for degree_facet in request_vars.get('degree_type')]
        filter_queries.append("(or %s)" % " ".join(degree_facets))
    elif request_vars.get('degree_type'):
        filter_queries.append("(term field=degree_type '%s')" % request_vars.get('degree_type'))

    if isinstance(request_vars.get('school_name'), list):
        # search for exact values in facets
        school_facets = ["school_name:'%s'" % school_facet for school_facet in request_vars.get('school_name')]
        filter_queries.append("(or %s)" % " ".join(school_facets))
    elif request_vars.get('school_name'):
        filter_queries.append("(term field=school_name '%s')" % request_vars.get('school_name'))

    if isinstance(request_vars.get('major'), list):
        # search for exact values in facets
        concentration_facets = ["concentration_type:'%s'" % concentration_facet for concentration_facet
                                in request_vars.get('major')]
        filter_queries.append("(and %s)" % " ".join(concentration_facets))
    elif request_vars.get('major'):
        filter_queries.append("(term field=concentration_type '%s')" % request_vars.get('major'))

    if request_vars.get('degree_end_year_from') or request_vars.get('degree_end_year_to'):
        from_datetime_str, to_datetime_str = _convert_date_range_in_cloudsearch_format(request_vars.get(
            'degree_end_year_from'), request_vars.get('degree_end_year_to'))
        if from_datetime_str and to_datetime_str:
            filter_queries.append("degree_end_date:%s,%s" % (from_datetime_str, to_datetime_str))

    if isinstance(request_vars.get('military_service_status'), list):
        # search for exact values in facets
        service_status_facets = ["military_service_status:'%s'" % service_status_facet for service_status_facet in
                                 request_vars.get('military_service_status')]
        filter_queries.append("(or %s)" % " ".join(service_status_facets))
    elif request_vars.get('military_service_status'):
        filter_queries.append("(term field=military_service_status '%s')" % request_vars.get('military_service_status'))

    if isinstance(request_vars.get('military_branch'), list):
        # search for exact values in facets
        branch_facets = ["military_branch:'%s'" % branch_facet for branch_facet in request_vars.get('military_branch')]
        filter_queries.append("(or %s)" % " ".join( branch_facets ))
    elif request_vars.get('military_branch'):
        filter_queries.append("(term field=military_branch '%s' )" % request_vars.get('military_branch'))

    if isinstance(request_vars.get('military_highest_grade'), list):
        # search for exact values in facets
        grade_facets = ["military_highest_grade:'%s'" % grade_facet for grade_facet in request_vars.get('military_highest_grade')]
        filter_queries.append("(or %s)" % " ".join(grade_facets))
    elif request_vars.get('military_highest_grade'):
        filter_queries.append("(term field=military_highest_grade '%s')" % request_vars.get('military_highest_grade'))

    # Date of separation - Military
    if request_vars.get('military_end_date_from') or request_vars.get('military_end_date_to'):
        from_datetime_str, to_datetime_str = _convert_date_range_in_cloudsearch_format(
            request_vars.get('military_end_date_from'), request_vars.get('military_end_date_to'))
        if from_datetime_str is not None and to_datetime_str is not None:
            filter_queries.append("military_end_date:%s,%s" % (from_datetime_str, to_datetime_str))
    # Handling custom fields
    for key, value in request_vars.items():
        if 'cf-' in key:
            filter_queries = filter_queries + _search_custom_fields(request_vars)

    filter_queries_list.append(filter_queries)

    # Get filter_query for each of the search_params dictionary and push it to filter_queries_list
    search_params_list = request_vars.get('search_params') or []
    if isinstance(search_params_list, list):
        for search_params in search_params_list:
            get_filter_query_from_request_vars(search_params)

    return filter_queries_list


def _clear_filter_queries_and_search_queries_list():
    if filter_queries_list or search_queries_list:
        filter_queries_list[:] = []
        search_queries_list[:] = []
