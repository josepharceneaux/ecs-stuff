"""
This file contains slightly changed logic for uploading candidate docs to Prod-us-west-1 AWS Cloud Search instance
"""
import time
import boto
import boto.exception
import simplejson
from sqlalchemy.sql import text
from candidate_service.candidate_app import app, logger
from candidate_service.common.utils.timeout import Timeout, TimeoutException
from candidate_service.common.talent_celery import OneTimeSQLConnection
from candidate_service.common.models.user import User
from candidate_service.common.talent_config_manager import TalentConfigKeys

MYSQL_DATE_FORMAT = '%Y-%m-%dT%H:%i:%S.%fZ'
BATCH_REQUEST_LIMIT_BYTES = 5 * 1024 * 1024
DOCUMENT_SIZE_LIMIT_BYTES = 1024 * 1024

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

INDEX_FIELD_NAME_TO_OPTIONS = {
    'id':                           dict(IndexFieldType='int',              IntOptions={'FacetEnabled': False}),
    'first_name':                   dict(IndexFieldType='text',             TextOptions={'Stopwords': STOPWORDS_JSON_ARRAY,
                                                                                         'HighlightEnabled': False}),
    'last_name':                     dict(IndexFieldType='text',            TextOptions={'Stopwords': STOPWORDS_JSON_ARRAY,
                                                                                         'HighlightEnabled': False}),
    'email':                         dict(IndexFieldType='text-array'),
    'user_id':                       dict(IndexFieldType='int'),
    'domain_id':                     dict(IndexFieldType='int',             IntOptions={'ReturnEnabled': False}),

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
    'state':                         dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': True}),
    'zip_code':                      dict(IndexFieldType='literal-array',   LiteralArrayOptions={'ReturnEnabled': False,
                                                                                                 'SortEnabled': False}),
    'coordinates':                   dict(IndexFieldType='latlon',          LatLonOptions={'ReturnEnabled': False,
                                                                                           'FacetEnabled': False}),

    # Experience
    'total_months_experience':       dict(IndexFieldType='int',             IntOptions={'ReturnEnabled': False}),
    'organization':                  dict(IndexFieldType='literal-array',   LiteralArrayOptions={'FacetEnabled': True}),
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
    'dumb_lists':                    dict(IndexFieldType='int-array',       IntArrayOptions={'ReturnEnabled': False}),
    'removed_talent_pipelines':      dict(IndexFieldType='int-array',       IntArrayOptions={'ReturnEnabled': False}),
    'start_date_at_current_job':     dict(IndexFieldType='date',            DateOptions={'FacetEnabled': False,
                                                                                         'ReturnEnabled': True}),
    'candidate_engagement_score':    dict(IndexFieldType='double',          DoubleOptions={'FacetEnabled': True,
                                                                                           'ReturnEnabled': False})
}


# Filter all text, text-array, literal and literal-array index fields
QUERY_OPTIONS = filter(lambda field: 'text' in field[1]['IndexFieldType'] or 'literal' in field[1]['IndexFieldType'],
                       INDEX_FIELD_NAME_TO_OPTIONS.items())

QUERY_OPTIONS = map(lambda option: option[0], QUERY_OPTIONS)

QUERY_OPTIONS.remove('position')
QUERY_OPTIONS.append('position^1.5')
QUERY_OPTIONS.remove('skill_description')
QUERY_OPTIONS.append('skill_description^1.2')

coordinates = []

_cloud_search_connection_layer_2 = None
_cloud_search_domain = None


def get_cloud_search_connection():
    """
    Get cloud search connection
    :return:
    """

    global _cloud_search_connection_layer_2, _cloud_search_domain
    if not _cloud_search_connection_layer_2:
        _cloud_search_connection_layer_2 = boto.connect_cloudsearch2(
            aws_access_key_id=app.config[TalentConfigKeys.AWS_KEY],
            aws_secret_access_key=app.config[TalentConfigKeys.AWS_SECRET],
            sign_request=True,
            region='us-west-1'
        )

        _cloud_search_domain = _cloud_search_connection_layer_2.lookup(app.config[TalentConfigKeys.CS_DOMAIN_KEY])
        if not _cloud_search_domain:
            _cloud_search_connection_layer_2.create_domain(app.config[TalentConfigKeys.CS_DOMAIN_KEY])

    return _cloud_search_connection_layer_2


def _build_candidate_documents(candidate_ids, domain_id=None):
    """
    Returns dicts like: {type="add", id="{candidate_id}", fields={dict of fields to values}}

    Note: Candidate fields must be exactly as they are defined in Cloud Search Index Field Names.
     Ex: candidate.firstName AS `first_name`
    """
    group_concat_separator = '~~~'

    sql_query = """
    SELECT
                # Candidate table info
                candidate.id AS `id`, candidate.firstName AS `first_name`, candidate.lastName AS `last_name`,
                candidate.statusId AS `status_id`, DATE_FORMAT(candidate.addedTime, :date_format) AS `added_time`,
                candidate.ownerUserId AS `user_id`, candidate.objective AS `objective`,
                candidate.is_archived AS `is_archived`, candidate.source_detail AS `source_details`,
                candidate.sourceId AS `source_id`,
                candidate.sourceProductId AS `source_product_id`, candidate.totalMonthsExperience AS
                `total_months_experience`,

                # Address & contact info
                candidate_address.city AS `city`, candidate_address.state AS `state`, candidate_address.zipCode AS `zip_code`,
                candidate_address.coordinates AS `coordinates`,
                GROUP_CONCAT(DISTINCT candidate_email.address SEPARATOR :sep) AS `email`,

                # Dumb Lists
                GROUP_CONCAT(DISTINCT smart_list_candidate.smartlistId SEPARATOR :sep) AS `dumb_lists`,

                # Pipelines to which candidate belongs statically
                GROUP_CONCAT(DISTINCT talent_pipeline_included_candidates.talent_pipeline_id SEPARATOR :sep) AS `added_talent_pipelines`,

                # Pipelines to which candidate doesn't belong at all
                GROUP_CONCAT(DISTINCT talent_pipeline_excluded_candidates.talent_pipeline_id SEPARATOR :sep) AS `removed_talent_pipelines`,

                # AOIs and Custom Fields
                GROUP_CONCAT(DISTINCT candidate_area_of_interest.areaOfInterestId SEPARATOR :sep) AS `area_of_interest_id`,
                GROUP_CONCAT(DISTINCT CONCAT(candidate_custom_field.customFieldId, '|', candidate_custom_field.value) SEPARATOR :sep) AS `custom_field_id_and_value`,

                # Military experience
                GROUP_CONCAT(DISTINCT candidate_military_service.highestGrade SEPARATOR :sep) AS `military_highest_grade`,
                GROUP_CONCAT(DISTINCT candidate_military_service.serviceStatus SEPARATOR :sep) AS `military_service_status`,
                GROUP_CONCAT(DISTINCT candidate_military_service.branch SEPARATOR :sep) AS `military_branch`,
                GROUP_CONCAT(DISTINCT DATE_FORMAT(candidate_military_service.toDate, :date_format) SEPARATOR :sep) AS `military_end_date`,

                # Experience
                GROUP_CONCAT(DISTINCT candidate_experience.organization SEPARATOR :sep) AS `organization`,
                GROUP_CONCAT(DISTINCT candidate_experience.position ORDER BY candidate_experience.IsCurrent DESC, candidate_experience.StartYear DESC, candidate_experience.StartMonth DESC SEPARATOR :sep) AS `position`,
                GROUP_CONCAT(DISTINCT candidate_experience_bullet.description SEPARATOR :sep) AS `experience_description`,

                # Start Date At Current Job
                DATE_FORMAT(MIN((CASE candidate_experience.IsCurrent WHEN 1 THEN DATE_ADD(MAKEDATE((CASE WHEN candidate_experience.StartYear then candidate_experience.StartYear ELSE YEAR(CURDATE()) END) , 1), INTERVAL (CASE WHEN candidate_experience.StartMonth then candidate_experience.StartMonth ELSE MONTH(CURDATE()) END)-1 MONTH) END)), :date_format) AS `start_date_at_current_job`,

                # Education
                GROUP_CONCAT(DISTINCT candidate_education.schoolName SEPARATOR :sep) AS `school_name`,
                GROUP_CONCAT(DISTINCT candidate_education_degree.degreeType SEPARATOR :sep) AS `degree_type`,
                GROUP_CONCAT(DISTINCT candidate_education_degree.degreeTitle SEPARATOR :sep) AS `degree_title`,
                GROUP_CONCAT(DISTINCT DATE_FORMAT(candidate_education_degree.endTime, :date_format) SEPARATOR :sep) AS `degree_end_date`,
                GROUP_CONCAT(DISTINCT candidate_education_degree_bullet.concentrationType SEPARATOR :sep) AS `concentration_type`,

                # Skill & unidentified
                GROUP_CONCAT(DISTINCT candidate_skill.description SEPARATOR :sep) AS `skill_description`,
                GROUP_CONCAT(DISTINCT candidate_unidentified.description SEPARATOR :sep) AS `unidentified_description`,

                # Rating and comments
                GROUP_CONCAT(DISTINCT CONCAT(candidate_rating.ratingTagId, '|', candidate_rating.value) SEPARATOR :sep) AS `candidate_rating_id_and_value`,
                GROUP_CONCAT(DISTINCT candidate_text_comment.comment SEPARATOR :sep) AS `text_comment`,

                # Tags
                GROUP_CONCAT(DISTINCT candidate_tag.tag_id SEPARATOR :sep) AS `tag_ids`

    FROM        candidate

    LEFT JOIN   smart_list_candidate ON (candidate.id = smart_list_candidate.candidateId)
    LEFT JOIN   talent_pipeline_included_candidates ON (candidate.id = talent_pipeline_included_candidates.candidate_id)
    LEFT JOIN   talent_pipeline_excluded_candidates ON (candidate.id = talent_pipeline_excluded_candidates.candidate_id)
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

    # Tags
    LEFT JOIN   candidate_tag ON (candidate.id = candidate_tag.candidate_id)

    WHERE       candidate.id IN :candidate_ids_string

    GROUP BY    candidate.id
    ;
    """

    action_dicts = []
    with OneTimeSQLConnection(app) as session:

        session.connection().execute('SET SESSION group_concat_max_len=50000;')

        results = session.connection().execute(text(sql_query),
                                               candidate_ids_string=tuple(candidate_ids),
                                               sep=group_concat_separator,
                                               date_format=MYSQL_DATE_FORMAT)

        # Go through results & build action dicts
        for field_name_to_sql_value in results:
            candidate_id = field_name_to_sql_value['id']

            action_dict = dict(type='add', id=str(candidate_id))

            # Remove keys with empty values
            field_name_to_sql_value = {k: v for k, v in field_name_to_sql_value.items() if v}

            # Add domain ID
            if not domain_id:
                field_name_to_sql_value_row = session.query(User).filter_by(
                    id=field_name_to_sql_value['user_id']).first()
                domain_id = field_name_to_sql_value_row.domain_id

            field_name_to_sql_value['domain_id'] = domain_id

            action_dict['fields'] = field_name_to_sql_value
            action_dicts.append(action_dict)

    return action_dicts


def upload_candidate_documents_to_us_west(candidate_ids, domain_id=None, max_number_of_candidate=10):
    """
    Upload all the candidate documents to cloud search
    :param candidate_ids: id of candidates for documents to be uploaded
    :param domain_id: Domain Id
    :param max_number_of_candidate: Default value is 10
    :return:
    """
    if isinstance(candidate_ids, (int, long)):
        candidate_ids = [candidate_ids]

    for i in xrange(0, len(candidate_ids), max_number_of_candidate):
        try:
            logger.info("Uploading {} candidate documents {}. Generating action dicts...".format(
                len(candidate_ids[i:i + max_number_of_candidate]), candidate_ids[i:i + max_number_of_candidate])
            )

            with Timeout(seconds=120):
                # If _build_candidate_documents take more than 120 seconds Timeout will raise an exception
                action_dicts = _build_candidate_documents(candidate_ids[i:i + max_number_of_candidate], domain_id)

            adds, deletes = _send_batch_request(action_dicts)
            if deletes:
                logger.error("Shouldn't have gotten any deletes in a batch add operation.Got %s "
                             "deletes.candidate_ids: %s", deletes, candidate_ids[i:i + max_number_of_candidate])
            if adds:
                logger.info("{} Candidate documents {} have been uploaded".format(
                    len(candidate_ids[i:i + max_number_of_candidate]), candidate_ids[i:i + max_number_of_candidate])
                )
        except TimeoutException:
            logger.exception("Time Limit Exceeded for Candidate Upload for following Candidates: {}".format(
                candidate_ids[i:i + max_number_of_candidate]))


def _send_batch_request(action_dicts):
    adds, deletes = 0, 0
    get_cloud_search_connection()
    import boto.cloudsearch2.document
    document_service_connection = boto.cloudsearch2.document.DocumentServiceConnection(domain=_cloud_search_domain)
    max_possible_request_size_bytes = 2  # Opening/closing brackets

    # If the batch request size > 5MB, split it up
    for i, action_dict in enumerate(action_dicts):
        try:
            action_dict_json = simplejson.dumps(action_dict, encoding='ISO-8859-1')
            action_dict = simplejson.loads(action_dict_json)
        except UnicodeDecodeError:
            print("talent_cloud_search._send_batch_request(): Couldn't encode action_dict to JSON: {}".format(action_dict))
            continue
        if len(action_dict_json) > DOCUMENT_SIZE_LIMIT_BYTES:
            # Individual doc size shouldn't exceed 1MB
            print("_send_batch_request: action dict was > 1MB, so couldn't send: {}".format(action_dict))
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
            except Exception as e:
                print("_send_batch_request: Exception when sending batch request: {}".format(e.message))
                result = None
            document_service_connection.clear_sdf()
            max_possible_request_size_bytes = 2
            if result:
                if result.errors:
                    print("Received errors committing action_dicts to CloudSearch: {}".format(result.errors))
                adds += result.adds
                deletes += result.deletes

    return adds, deletes


# if __name__ == '__main__':
#     print "~~~~~ STARTING UPLOAD CANDIDATE DOCS SCRIPT ~~~~~"
#     start_time = time.time()
#     try:
#         from candidate_service.common.models.candidate import Candidate
#         kaiser_candidates = Candidate.query.filter_by(source_id=6739)
#         candidate_ids = [2881510, 2881509, 2881508, 2881506]
#         upload_candidate_documents(candidate_ids)
#         print "~~~~~ UPLOAD SUCCESSFUL ~~~~~"
#     except Exception as e:
#         print("ERROR: {}".format(e.message))
