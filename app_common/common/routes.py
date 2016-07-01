"""
This file contains API REST endpoints of all services e.g. one of the endpoint of auth_service is
    /v1/oauth2/token.

This also contains complete URLs of REST endpoints of all services. e.g. for above example,
complete URL will be 127.0.0.1:8011/v1/oauth2/token

Here we have two classes for each service.
 e.g. for candidate_service
 1) CandidateApi which contains REST endpoints
 2) CandidateApiUrl which contains complete URLs of REST endpoints

"""
import os
from talent_config_manager import TalentConfigKeys, TalentEnvs

LOCAL_HOST = 'http://127.0.0.1'
TALENT_DOMAIN = '.gettalent.com'
HEALTH_CHECK = '/healthcheck'


def _get_host_name(service_name, port_number):
    """
    This function gives the Base API Url depending on the environment variable.
    If api_version is provided, it also appends the version of API.

    For DEV, CIRCLE, In case of auth_service we'll get

            http://127.0.0.1:8001%s
    For QA:
            http://auth-service-staging.gettalent.com (for auth service)
    For PROD:
            http://auth-service.gettalent.com (for auth service)

    :param service_name: Name of service
    :param port_number: Port number of service
    :type service_name: str
    :type port_number: int
    :return:  A string that looks like https://auth-service.gettalent.com%s
    """
    env = os.getenv(TalentConfigKeys.ENV_KEY) or TalentEnvs.DEV
    if env == TalentEnvs.DEV:
        # This looks like http://127.0.0.1:8001 (for auth service)
        return LOCAL_HOST + ':' + str(port_number) + '%s'
    elif env == TalentEnvs.JENKINS:
        return 'http://jenkins.gettalent.com' + ':' + str(port_number) + '%s'
    elif env == TalentEnvs.QA:
        # This looks like:  https://auth-service-staging.gettalent.com%s
        return 'https://' + service_name + '-staging' + TALENT_DOMAIN + '%s'
    elif env == TalentEnvs.PROD:
        # This looks like: https://auth-service.gettalent.com%s
        return 'https://' + service_name + TALENT_DOMAIN + '%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly: "
                        "Should be %s, %s, %s or %s"
                        % (TalentEnvs.DEV, TalentEnvs.JENKINS, TalentEnvs.QA, TalentEnvs.PROD))


def get_web_app_url():
    env = os.getenv(TalentConfigKeys.ENV_KEY) or TalentEnvs.DEV
    if env in (TalentEnvs.DEV, TalentEnvs.JENKINS):
        return LOCAL_HOST + ':3000'
    elif env == TalentEnvs.QA:
        return 'https://staging.gettalent.com'
    elif env == TalentEnvs.PROD:
        return 'https://app.gettalent.com'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly: "
                        "Should be %s, %s, %s or %s"
                        % (TalentEnvs.DEV, TalentEnvs.JENKINS, TalentEnvs.QA, TalentEnvs.PROD))


def _get_health_check_url(host_name):
    """
    This returns the healthcheck url appended with host name. e.g.http://127.0.0.1:8001/healthcheck
    :param str host_name: name of host. e.g.http://127.0.0.1:8001
    """
    return host_name % HEALTH_CHECK


class GTApis(object):
    """
    This class contains the getTalent flask micro services' name and respective port numbers.
    """

    # Port Numbers of Flask micro services
    AUTH_SERVICE_PORT = 8001
    ACTIVITY_SERVICE_PORT = 8002
    RESUME_PARSING_SERVICE_PORT = 8003
    USER_SERVICE_PORT = 8004
    CANDIDATE_SERVICE_PORT = 8005
    WIDGET_SERVICE_PORT = 8006
    SOCIAL_NETWORK_SERVICE_PORT = 8007
    CANDIDATE_POOL_SERVICE_PORT = 8008
    SPREADSHEET_IMPORT_SERVICE_PORT = 8009
    DASHBOARD_SERVICE_PORT = 8010
    SCHEDULER_SERVICE_PORT = 8011
    SMS_CAMPAIGN_SERVICE_PORT = 8012
    PUSH_CAMPAIGN_SERVICE_PORT = 8013
    EMAIL_CAMPAIGN_SERVICE_PORT = 8014
    ATS_SERVICE_PORT = 8015

    # Names of flask micro services
    AUTH_SERVICE_NAME = 'auth-service'
    ACTIVITY_SERVICE_NAME = 'activity-service'
    RESUME_PARSING_SERVICE_NAME = 'resume-parsing-service'
    USER_SERVICE_NAME = 'user-service'
    CANDIDATE_SERVICE_NAME = 'candidate-service'
    WIDGET_SERVICE_NAME = 'widget-service'
    SOCIAL_NETWORK_SERVICE_NAME = 'social-network-service'
    CANDIDATE_POOL_SERVICE_NAME = 'candidate-pool-service'
    SPREADSHEET_IMPORT_SERVICE_NAME = 'spreadsheet-import-service'
    DASHBOARD_SERVICE_NAME = 'frontend-service'
    SCHEDULER_SERVICE_NAME = 'scheduler-service'
    SMS_CAMPAIGN_SERVICE_NAME = 'sms-campaign-service'
    PUSH_CAMPAIGN_SERVICE_NAME = 'push-campaign-service'
    EMAIL_CAMPAIGN_SERVICE_NAME = 'email-campaign-service'
    ATS_SERVICE_NAME = 'ats-service'

    # CORS headers
    CORS_HEADERS = {r"*": {"origins": [r".*\.gettalent\.com",
                                       "http://127.0.0.1",
                                       "https://127.0.0.1",
                                       "http://localhost"]}}


class AuthApi(object):
    """
    API relative URLs for auth_service. e.g. /v1/oauth2/token
    """
    VERSION = 'v1'
    TOKEN_CREATE = '/' + VERSION + '/oauth2/token'
    TOKEN_REVOKE = '/' + VERSION + '/oauth2/revoke'
    AUTHORIZE = '/' + VERSION + '/oauth2/authorize'
    TOKEN_OF_ANY_USER = '/' + VERSION + 'users/<int:user_id>/token'


class AuthApiUrl(object):
    """
    Rest URLs of auth_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.AUTH_SERVICE_NAME, GTApis.AUTH_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    TOKEN_CREATE = HOST_NAME % ('/' + VERSION + '/oauth2/token')
    TOKEN_REVOKE = HOST_NAME % ('/' + VERSION + '/oauth2/revoke')
    AUTHORIZE = HOST_NAME % ('/' + VERSION + '/oauth2/authorize')
    TOKEN_OF_ANY_USER_URL = HOST_NAME % ('/' + VERSION + 'users/%s/token')


class AuthApiV2(object):
    """
    API relative URLs for auth_service. e.g. /v2/oauth2/token
    """
    VERSION = 'v2'
    TOKEN_CREATE = '/' + VERSION + '/oauth2/token'
    TOKEN_REFRESH = '/' + VERSION + '/oauth2/refresh'
    TOKEN_REVOKE = '/' + VERSION + '/oauth2/revoke'
    AUTHORIZE = '/' + VERSION + '/oauth2/authorize'
    TOKEN_OF_ANY_USER = '/' + VERSION + 'users/<int:user_id>/token'


class AuthApiUrlV2(object):
    """
    Rest URLs of auth_service
    """
    VERSION = 'v2'
    HOST_NAME = _get_host_name(GTApis.AUTH_SERVICE_NAME, GTApis.AUTH_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    TOKEN_CREATE = HOST_NAME % ('/' + VERSION + '/oauth2/token')
    TOKEN_REFRESH = HOST_NAME % ('/' + VERSION + '/oauth2/refresh')
    TOKEN_REVOKE = HOST_NAME % ('/' + VERSION + '/oauth2/revoke')
    AUTHORIZE = HOST_NAME % ('/' + VERSION + '/oauth2/authorize')
    TOKEN_OF_ANY_USER_URL = HOST_NAME % ('/' + VERSION + 'users/%s/token')


class ActivityApi(object):
    """
    API relative URLs for activity_service. e.g /v1/activities/
    """
    VERSION = 'v1'
    # /v1/activities/
    ACTIVITIES = '/' + VERSION + '/activities/'
    # /v1/activities/<page>
    ACTIVITIES_PAGE = '/' + VERSION + '/activities/<page>'
    ACTIVITY_MESSAGES = '/' + VERSION + '/messages'
    LAST_READ = '/' + VERSION + '/last-read'


class ActivityApiUrl(object):
    """
    Rest URLs of activity_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.ACTIVITY_SERVICE_NAME, GTApis.ACTIVITY_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    ACTIVITIES = HOST_NAME % ('/' + VERSION + '/activities/')
    ACTIVITIES_PAGE = HOST_NAME % ('/' + VERSION + '/activities/%s')


class ResumeApi(object):
    """
    API relative URLs for resume_parsing_service. e.g. /v1/parse_resume
    """
    VERSION = 'v1'
    URL_PREFIX = '/' + VERSION + '/'
    PARSE = 'parse_resume'
    BATCH = 'batch'


class ResumeApiUrl(object):
    """
    Rest URLs of resume_parsing_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.RESUME_PARSING_SERVICE_NAME, GTApis.RESUME_PARSING_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    BASE_URL = HOST_NAME % ('/' + VERSION + '/%s')
    PARSE = HOST_NAME % ('/' + VERSION + '/parse_resume')
    BATCH_URL = HOST_NAME % ('/' + VERSION + '/batch')
    BATCH_PROCESS = HOST_NAME % ('/' + VERSION + '/batch/<int:user_id>')


class UserServiceApi(object):
    """
    API relative URLs for user_service. e.g. /v1/users
    """
    VERSION = 'v1'
    URL_PREFIX = '/' + VERSION + '/'
    USERS = "users"
    USER = "users/<int:id>"
    USER_INVITE = "users/<int:id>/invite"

    DOMAINS = "domains"
    DOMAIN = "domains/<int:id>"
    USER_ROLES = "users/<int:user_id>/roles"
    DOMAIN_ROLES = "domain/<int:domain_id>/roles"
    DOMAIN_GROUPS = "domain/<int:domain_id>/groups"
    DOMAIN_GROUPS_UPDATE = "domain/groups/<int:group_id>"
    USER_GROUPS = "groups/<int:group_id>/users"
    UPDATE_PASSWORD = "users/update-password"
    FORGOT_PASSWORD = "users/forgot-password"
    RESET_PASSWORD = "users/reset-password/<token>"

    DOMAIN_SOURCES = '/' + VERSION + '/sources'
    DOMAIN_SOURCE = '/' + VERSION + '/sources/<int:id>'
    DOMAIN_CUSTOM_FIELDS = '/' + VERSION + '/custom_fields'
    DOMAIN_CUSTOM_FIELD = DOMAIN_CUSTOM_FIELDS + '/<int:id>'
    DOMAIN_AOIS = '/' + VERSION + '/areas_of_interest'
    DOMAIN_AOI = '/' + VERSION + '/areas_of_interest/<int:id>'


class UserServiceApiUrl(object):
    """
    Rest URLs of user_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.USER_SERVICE_NAME, GTApis.USER_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    USERS = HOST_NAME % ('/' + VERSION + '/users')
    USER = HOST_NAME % ('/' + VERSION + '/users/%s')
    USER_INVITE = HOST_NAME % ('/' + VERSION + '/users/%s/invite')
    DOMAINS = HOST_NAME % ('/' + VERSION + '/domains')
    DOMAIN = HOST_NAME % ('/' + VERSION + '/domains/%s')
    USER_ROLES_API = HOST_NAME % ('/' + VERSION + '/users/%s/roles')
    DOMAIN_ROLES_API = HOST_NAME % ('/' + VERSION + '/domain/%s/roles')
    DOMAIN_GROUPS_API = HOST_NAME % ('/' + VERSION + '/domain/%s/groups')
    DOMAIN_GROUPS_UPDATE_API = HOST_NAME % ('/' + VERSION + '/domain/groups/%s')

    DOMAIN_SOURCES = HOST_NAME % ('/' + VERSION + '/sources')
    DOMAIN_SOURCE = HOST_NAME % ('/' + VERSION + '/sources/%s')

    USER_GROUPS_API = HOST_NAME % ('/' + VERSION + '/groups/%s/users')
    UPDATE_PASSWORD_API = HOST_NAME % ('/' + VERSION + '/users/update-password')
    FORGOT_PASSWORD_API = HOST_NAME % ('/' + VERSION + '/users/forgot-password')
    RESET_PASSWORD_API = HOST_NAME % ('/' + VERSION + '/users/reset-password/%s')
    DOMAIN_CUSTOM_FIELDS = HOST_NAME % ('/' + VERSION + '/custom_fields')
    DOMAIN_CUSTOM_FIELD = DOMAIN_CUSTOM_FIELDS + '/%s'
    DOMAIN_AOIS = HOST_NAME % ('/' + VERSION + '/areas_of_interest')
    DOMAIN_AOI = HOST_NAME % ('/' + VERSION + '/areas_of_interest/%s')


class CandidateApi(object):
    """
    API relative URLs for candidate_service. e.g /v1/candidates
    """
    VERSION = 'v1'

    CANDIDATES = '/' + VERSION + '/candidates'
    CANDIDATE_ID = '/' + VERSION + '/candidates/<int:id>'
    CANDIDATE_EMAIL = '/' + VERSION + '/candidates/<email>'

    ADDRESSES = '/' + VERSION + '/candidates/<int:candidate_id>/addresses'
    ADDRESS = '/' + VERSION + '/candidates/<int:candidate_id>/addresses/<int:id>'

    AOIS = '/' + VERSION + '/candidates/<int:candidate_id>/areas_of_interest'
    AOI = '/' + VERSION + '/candidates/<int:candidate_id>/areas_of_interest/<int:id>'

    CUSTOM_FIELDS = '/' + VERSION + '/candidates/<int:candidate_id>/custom_fields'
    CUSTOM_FIELD = '/' + VERSION + '/candidates/<int:candidate_id>/custom_fields/<int:id>'

    EDUCATIONS = '/' + VERSION + '/candidates/<int:candidate_id>/educations'
    EDUCATION = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:id>'

    DEGREES = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:education_id>/degrees'
    DEGREE = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:id>'

    DEGREE_BULLETS = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:degree_id>/bullets'
    DEGREE_BULLET = '/' + VERSION + '/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:degree_id>/bullets/<int:id>'

    DEVICES = '/' + VERSION + '/candidates/<int:id>/devices'
    DEVICE = '/' + VERSION + '/candidates/<int:id>/devices/<int:id>'

    EXPERIENCES = '/' + VERSION + '/candidates/<int:candidate_id>/work_experiences'
    EXPERIENCE = '/' + VERSION + '/candidates/<int:candidate_id>/work_experiences/<int:id>'

    EXPERIENCE_BULLETS = '/' + VERSION + '/candidates/<int:candidate_id>/work_experiences/<int:experience_id>/bullets'
    EXPERIENCE_BULLET = '/' + VERSION + '/candidates/<int:candidate_id>/work_experiences/<int:experience_id>/bullets/<int:id>'

    EMAILS = '/' + VERSION + '/candidates/<int:candidate_id>/emails'
    EMAIL = '/' + VERSION + '/candidates/<int:candidate_id>/emails/<int:id>'

    MILITARY_SERVICES = '/' + VERSION + '/candidates/<int:candidate_id>/military_services'
    MILITARY_SERVICE = '/' + VERSION + '/candidates/<int:candidate_id>/military_services/<int:id>'

    PHONES = '/' + VERSION + '/candidates/<int:candidate_id>/phones'
    PHONE = '/' + VERSION + '/candidates/<int:candidate_id>/phones/<int:id>'

    PREFERRED_LOCATIONS = '/' + VERSION + '/candidates/<int:candidate_id>/preferred_locations'
    PREFERRED_LOCATION = '/' + VERSION + '/candidates/<int:candidate_id>/preferred_locations/<int:id>'

    SKILLS = '/' + VERSION + '/candidates/<int:candidate_id>/skills'
    SKILL = '/' + VERSION + '/candidates/<int:candidate_id>/skills/<int:id>'

    PHOTOS = '/' + VERSION + '/candidates/<int:candidate_id>/photos'
    PHOTO = '/' + VERSION + '/candidates/<int:candidate_id>/photos/<int:id>'

    SOCIAL_NETWORKS = '/' + VERSION + '/candidates/<int:candidate_id>/social_networks'
    SOCIAL_NETWORK = '/' + VERSION + '/candidates/<int:candidate_id>/social_networks/<int:id>'

    WORK_PREFERENCES = '/' + VERSION + '/candidates/<int:candidate_id>/work_preferences'
    WORK_PREFERENCE = '/' + VERSION + '/candidates/<int:candidate_id>/work_preferences/<int:id>'
    CANDIDATE_EDIT = '/' + VERSION + '/candidates/<int:id>/edits'

    CANDIDATE_SEARCH = '/' + VERSION + '/candidates/search'
    CANDIDATES_DOCUMENTS = '/' + VERSION + '/candidates/documents'
    OPENWEB = '/' + VERSION + '/candidates/openweb'
    CANDIDATE_CLIENT_CAMPAIGN = '/' + VERSION + '/candidates/client_email_campaign'
    CANDIDATE_VIEWS = '/' + VERSION + '/candidates/<int:id>/views'
    CANDIDATE_PREFERENCES = '/' + VERSION + '/candidates/<int:id>/preferences'

    CANDIDATE_NOTES = '/' + VERSION + '/candidates/<int:candidate_id>/notes'
    CANDIDATE_NOTE = CANDIDATE_NOTES + '/<int:id>'

    LANGUAGES = '/' + VERSION + '/candidates/<int:candidate_id>/languages'
    LANGUAGE = '/' + VERSION + '/candidates/<int:candidate_id>/languages/<int:id>'

    REFERENCES = '/' + VERSION + '/candidates/<int:candidate_id>/references'
    REFERENCE = '/' + VERSION + '/candidates/<int:candidate_id>/references/<int:id>'

    TAGS = '/' + VERSION + '/candidates/<int:candidate_id>/tags'
    TAG = '/' + VERSION + '/candidates/<int:candidate_id>/tags/<int:id>'

    PIPELINES = '/' + VERSION + '/candidates/<int:candidate_id>/pipelines'
    STATUSES = '/' + VERSION + '/candidate_statuses'


class CandidateApiUrl(object):
    """
    Rest URLs of candidate_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_SERVICE_NAME, GTApis.CANDIDATE_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    CANDIDATES = HOST_NAME % ('/' + VERSION + '/candidates')
    CANDIDATE = HOST_NAME % ('/' + VERSION + '/candidates/%s')

    ADDRESSES = HOST_NAME % ('/' + VERSION + '/candidates/%s/addresses')
    ADDRESS = HOST_NAME % ('/' + VERSION + '/candidates/%s/addresses/%s')

    AOIS = HOST_NAME % ('/' + VERSION + '/candidates/%s/areas_of_interest')
    AOI = HOST_NAME % ('/' + VERSION + '/candidates/%s/areas_of_interest/%s')

    CUSTOM_FIELDS = HOST_NAME % ('/' + VERSION + '/candidates/%s/custom_fields')
    CUSTOM_FIELD = CUSTOM_FIELDS + "/%s"

    CANDIDATE_SEARCH_URI = HOST_NAME % ('/' + VERSION + '/candidates/search')

    CANDIDATES_DOCUMENTS_URI = HOST_NAME % ('/' + VERSION + '/candidates/documents')

    EDUCATIONS = HOST_NAME % ('/' + VERSION + '/candidates/%s/educations')
    EDUCATION = HOST_NAME % ('/' + VERSION + '/candidates/%s/educations/%s')

    DEGREES = HOST_NAME % ('/' + VERSION + '/candidates/%s/educations/%s/degrees')
    DEGREE = HOST_NAME % ('/' + VERSION + '/candidates/%s/educations/%s/degrees/%s')

    DEGREE_BULLETS = HOST_NAME % ('/' + VERSION + '/candidates/%s/educations/%s/degrees/%s/bullets')
    DEGREE_BULLET = HOST_NAME % ('/' + VERSION + '/candidates/%s/educations/%s/degrees/%s/bullets/%s')

    DEVICES = HOST_NAME % ('/' + VERSION + '/candidates/%s/devices')
    DEVICE = HOST_NAME % ('/' + VERSION + '/candidates/%s/devices/%s')

    EMAILS = HOST_NAME % ('/' + VERSION + '/candidates/%s/emails')
    EMAIL = HOST_NAME % ('/' + VERSION + '/candidates/%s/emails/%s')

    EXPERIENCES = HOST_NAME % ('/' + VERSION + '/candidates/%s/work_experiences')
    EXPERIENCE = HOST_NAME % ('/' + VERSION + '/candidates/%s/work_experiences/%s')

    EXPERIENCE_BULLETS = HOST_NAME % ('/' + VERSION + '/candidates/%s/work_experiences/%s/bullets')
    EXPERIENCE_BULLET = HOST_NAME % ('/' + VERSION + '/candidates/%s/work_experiences/%s/bullets/%s')

    MILITARY_SERVICES = HOST_NAME % ('/' + VERSION + '/candidates/%s/military_services')
    MILITARY_SERVICE = HOST_NAME % ('/' + VERSION + '/candidates/%s/military_services/%s')

    PHONES = HOST_NAME % ('/' + VERSION + '/candidates/%s/phones')
    PHONE = HOST_NAME % ('/' + VERSION + '/candidates/%s/phones/%s')

    PREFERRED_LOCATIONS = HOST_NAME % ('/' + VERSION + '/candidates/%s/preferred_locations')
    PREFERRED_LOCATION = HOST_NAME % ('/' + VERSION + '/candidates/%s/preferred_locations/%s')

    SKILLS = HOST_NAME % ('/' + VERSION + '/candidates/%s/skills')
    SKILL = HOST_NAME % ('/' + VERSION + '/candidates/%s/skills/%s')

    PHOTOS = HOST_NAME % ('/' + VERSION + '/candidates/%s/photos')
    PHOTO = HOST_NAME % ('/' + VERSION + '/candidates/%s/photos/%s')

    SOCIAL_NETWORKS = HOST_NAME % ('/' + VERSION + '/candidates/%s/social_networks')
    SOCIAL_NETWORK = HOST_NAME % ('/' + VERSION + '/candidates/%s/social_networks/%s')

    WORK_PREFERENCES = HOST_NAME % ('/' + VERSION + '/candidates/%s/work_preferences')
    WORK_PREFERENCE_ID = HOST_NAME % ('/' + VERSION + '/candidates/%s/work_preferences/%s')
    CANDIDATE_EDIT = HOST_NAME % ('/' + VERSION + '/candidates/%s/edits')
    CANDIDATE_VIEW = HOST_NAME % ('/' + VERSION + '/candidates/%s/views')
    CANDIDATE_PREFERENCE = HOST_NAME % ('/' + VERSION + '/candidates/%s/preferences')

    NOTES = HOST_NAME % ('/' + VERSION + '/candidates/%s/notes')
    NOTE = NOTES + '/%s'

    CANDIDATE_CLIENT_CAMPAIGN = HOST_NAME % ('/' + VERSION + '/candidates/client_email_campaign')

    LANGUAGES = HOST_NAME % ('/' + VERSION + '/candidates/%s/languages')
    LANGUAGE = HOST_NAME % ('/' + VERSION + '/candidates/%s/languages/%s')

    REFERENCES = HOST_NAME % ('/' + VERSION + '/candidates/%s/references')
    REFERENCE = HOST_NAME % ('/' + VERSION + '/candidates/%s/references/%s')

    TAGS = HOST_NAME % ('/' + VERSION + '/candidates/%s/tags')
    TAG = HOST_NAME % ('/' + VERSION + '/candidates/%s/tags/%s')

    PIPELINES = HOST_NAME % ('/' + VERSION + '/candidates/%s/pipelines')
    STATUSES = HOST_NAME % ('/' + VERSION + '/candidate_statuses')


class WidgetApi(object):
    """
    API relative URLs for widget_service. e.g. /v1/universities
    """
    VERSION = 'v1'
    URL_PREFIX = '/' + VERSION + '/'
    DOMAINS = 'domains'
    DOMAIN_WIDGETS = 'domains/<path:encrypted_domain_id>/widgets/<path:encrypted_widget_id>'
    DOMAIN_INTERESTS = 'domains/<path:encrypted_domain_id>/interests'
    DOMAIN_MAJORS = 'domains/<path:encrypted_domain_id>/majors'
    UNIVERSITIES = 'universities'


class WidgetApiUrl(object):
    """
    Rest URLs of widget_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.WIDGET_SERVICE_NAME, GTApis.WIDGET_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    DOMAINS = HOST_NAME % ('/' + VERSION + '/domains')
    DOMAIN_WIDGETS = HOST_NAME % ('/' + VERSION + '/domains/%s/widgets/%s')
    DOMAIN_INTERESTS = HOST_NAME % ('/' + VERSION + '/domains/%s/interests')
    DOMAIN_MAJORS = HOST_NAME % ('/' + VERSION + '/domains/%s/majors')
    UNIVERSITIES = HOST_NAME % ('/' + VERSION + '/universities')


class CandidatePoolApi(object):
    """
    API relative URLs for candidate_pool_service. e.g. /v1/smartlists
    """
    VERSION = 'v1'
    # /v1/
    URL_PREFIX = '/' + VERSION + '/'
    # Talent Pools
    TALENT_POOLS = 'talent-pools'
    TALENT_POOL = 'talent-pools/<int:id>'
    TALENT_POOL_CANDIDATES = 'talent-pools/<int:id>/candidates'
    TALENT_PIPELINES_OF_TALENT_POOLS = 'talent-pools/<int:id>/talent-pipelines'
    TALENT_POOL_GROUPS = 'groups/<int:group_id>/talent-pools'
    TALENT_POOL_UPDATE_STATS = 'talent-pools/stats'
    TALENT_POOL_GET_STATS = 'talent-pools/<int:talent_pool_id>/stats'
    TALENT_PIPELINES_IN_TALENT_POOL_GET_STATS = 'talent-pools/<int:talent_pool_id>/talent-pipelines/stats'
    # Talent Pipelines
    TALENT_PIPELINES = 'talent-pipelines'
    TALENT_PIPELINE = 'talent-pipelines/<int:id>'
    TALENT_PIPELINE_SMARTLISTS = 'talent-pipelines/<int:id>/smartlists'
    TALENT_PIPELINE_CANDIDATES = 'talent-pipelines/<int:id>/candidates'
    TALENT_PIPELINE_ENGAGED_CANDIDATES = 'talent-pipelines/<int:id>/candidates/engagement'
    CANDIDATES_ENGAGED_TALENT_PIPELINES = 'candidates/<int:id>/talent-pipelines'
    TALENT_PIPELINE_CAMPAIGNS = 'talent-pipelines/<int:id>/campaigns'
    TALENT_PIPELINE_UPDATE_STATS = 'talent-pipelines/stats'
    TALENT_PIPELINE_GET_STATS = 'talent-pipelines/<int:talent_pipeline_id>/stats'
    # Smartlists
    SMARTLISTS = 'smartlists'
    SMARTLIST = 'smartlists/<int:id>'
    SMARTLIST_CANDIDATES = 'smartlists/<int:smartlist_id>/candidates'
    SMARTLIST_UPDATE_STATS = 'smartlists/stats'
    SMARTLIST_GET_STATS = 'smartlists/<int:smartlist_id>/stats'
    SMARTLIST_IN_TALENT_PIPELINE_GET_STATS = 'talent-pipelines/<int:talent_pipeline_id>/smartlists/stats'


class CandidatePoolApiUrl(object):
    """
    Rest URLs of candidate_pool_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.CANDIDATE_POOL_SERVICE_NAME, GTApis.CANDIDATE_POOL_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    # Talent Pool
    TALENT_POOLS = HOST_NAME % ('/' + VERSION + '/talent-pools')
    TALENT_POOL = HOST_NAME % ('/' + VERSION + '/talent-pools/%s')
    TALENT_POOL_CANDIDATE = HOST_NAME % ('/' + VERSION + '/talent-pools/%s/candidates')
    TALENT_PIPELINES_OF_TALENT_POOLS = HOST_NAME % ('/' + VERSION + '/talent-pools/%s/talent-pipelines')
    TALENT_POOL_GROUP = HOST_NAME % ('/' + VERSION + '/groups/%s/talent-pools')
    TALENT_POOL_UPDATE_STATS = HOST_NAME % ('/' + VERSION + '/talent-pools/stats')
    TALENT_POOL_GET_STATS = HOST_NAME % ('/' + VERSION + '/talent-pools/%s/stats')
    TALENT_PIPELINES_IN_TALENT_POOL_GET_STATS = \
        HOST_NAME % ('/' + VERSION + '/talent-pools/<int:talent_pool_id>/talent-pipelines/stats')
    # Talent Pipeline
    TALENT_PIPELINES = HOST_NAME % ('/' + VERSION + '/talent-pipelines')
    TALENT_PIPELINE = HOST_NAME % ('/' + VERSION + '/talent-pipelines/%s')
    TALENT_PIPELINE_SMARTLISTS = HOST_NAME % ('/' + VERSION + '/talent-pipelines/%s/smartlists')
    TALENT_PIPELINE_CANDIDATE = HOST_NAME % ('/' + VERSION + '/talent-pipelines/%s/candidates')
    TALENT_PIPELINE_CAMPAIGN = HOST_NAME % ('/' + VERSION + '/talent-pipelines/%s/campaigns')
    TALENT_PIPELINE_UPDATE_STATS = HOST_NAME % ('/' + VERSION + '/talent-pipelines/stats')
    TALENT_PIPELINE_GET_STATS = HOST_NAME % ('/' + VERSION + '/talent-pipelines/%s/stats')
    # Smartlists
    SMARTLISTS = HOST_NAME % ('/' + VERSION + '/smartlists')
    SMARTLIST = HOST_NAME % ('/' + VERSION + '/smartlists/%s')
    SMARTLIST_CANDIDATES = HOST_NAME % ('/' + VERSION + '/smartlists/%s/candidates')
    SMARTLIST_UPDATE_STATS = HOST_NAME % ('/' + VERSION + '/smartlists/stats')
    SMARTLIST_GET_STATS = HOST_NAME % ('/' + VERSION + '/smartlists/%s/stats')


class SpreadsheetImportApi(object):
    """
    API relative URLs for spreadsheet_import_service. e.g. /v1/parse_spreadsheet/convert_to_table
    """
    VERSION = 'v1'
    # This is /v1/
    URL_PREFIX = '/' + VERSION + '/'
    CONVERT_TO_TABLE = 'parse_spreadsheet/convert_to_table'
    IMPORT_CANDIDATES = 'parse_spreadsheet/import_candidates'


class SpreadsheetImportApiUrl(object):
    """
    Rest URLs of spreadsheet_import_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.SPREADSHEET_IMPORT_SERVICE_NAME, GTApis.SPREADSHEET_IMPORT_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    CONVERT_TO_TABLE = HOST_NAME % ('/' + VERSION + '/parse_spreadsheet/convert_to_table')
    IMPORT_CANDIDATES = HOST_NAME % ('/' + VERSION + '/parse_spreadsheet/import_candidates')


class SchedulerApi(object):
    """
    Rest Relative URLs of scheduler_service
    """
    VERSION = 'v1'
    # URLs, in case of API
    SCHEDULER_MULTIPLE_TASKS = '/' + VERSION + '/tasks'
    SCHEDULER_ONE_TASK = '/' + VERSION + '/tasks/id/<string:_id>'
    SCHEDULER_NAMED_TASK = '/' + VERSION + '/tasks/name/<string:_name>'
    SCHEDULER_ONE_TASK_NAME = '/' + VERSION + '/tasks/name/<string:_name>'
    SCHEDULER_MULTIPLE_TASK_RESUME = '/' + VERSION + '/tasks/resume'
    SCHEDULER_MULTIPLE_TASK_PAUSE = '/' + VERSION + '/tasks/pause'
    SCHEDULER_SINGLE_TASK_RESUME = '/' + VERSION + '/tasks/<string:_id>/resume'
    SCHEDULER_SINGLE_TASK_PAUSE = '/' + VERSION + '/tasks/<string:_id>/pause'
    SCHEDULER_ADMIN_TASKS = '/' + VERSION + '/admin/tasks'

    # Test endpoints for scheduler service
    SCHEDULER_TASKS_TEST = '/' + VERSION + '/tasks/test'
    SCHEDULER_TASKS_TEST_POST = '/' + VERSION + "/tasks/test-post"


class SchedulerApiUrl(object):
    """
    Rest URLs of scheduler_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.SCHEDULER_SERVICE_NAME, GTApis.SCHEDULER_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    # URLs, in case of test cases
    TASKS = HOST_NAME % ('/' + VERSION + '/tasks')
    TASK = HOST_NAME % ('/' + VERSION + '/tasks/id/%s')
    TASK_NAME = HOST_NAME % ('/' + VERSION + '/tasks/name/%s')
    PAUSE_TASK = HOST_NAME % ('/' + VERSION + '/tasks/%s/pause')
    RESUME_TASK = HOST_NAME % ('/' + VERSION + '/tasks/%s/resume')
    PAUSE_TASKS = HOST_NAME % ('/' + VERSION + '/tasks/pause')
    RESUME_TASKS = HOST_NAME % ('/' + VERSION + '/tasks/resume')

    # Scheduler Admin API
    ADMIN_TASKS = HOST_NAME % ('/' + VERSION + '/admin/tasks')

    # Use different port of scheduler service URL
    FLOWER_MONITORING_PORT = '--port=5511'

    # Test URLs for scheduler service
    TEST_TASK = HOST_NAME % ('/' + VERSION + '/tasks/test')
    TEST_TASK_POST = HOST_NAME % ('/' + VERSION + '/tasks/test-post')


class SocialNetworkApi(object):
    """
    Rest URLs for social_network_service
    """
    VERSION = 'v1'
    # URLs, in case of API
    EVENTS = '/' + VERSION + '/events'
    EVENT = '/' + VERSION + '/events/<int:event_id>'
    SOCIAL_NETWORKS = '/' + VERSION + '/social-networks'
    MEETUP_GROUPS = '/' + VERSION + '/social-networks/meetup-groups'
    TOKEN_VALIDITY = '/' + VERSION + '/social-networks/<int:social_network_id>/token/validity'
    TOKEN_REFRESH = '/' + VERSION + '/social-networks/<int:social_network_id>/token/refresh'
    USER_SOCIAL_NETWORK_CREDENTIALS = '/' + VERSION + '/social-networks/<int:social_network_id>/user/credentials'
    VENUES = '/' + VERSION + '/venues'
    VENUE = '/' + VERSION + '/venues/<int:venue_id>'
    EVENT_ORGANIZERS = '/' + VERSION + '/event-organizers'
    EVENT_ORGANIZER = '/' + VERSION + '/event-organizers/<int:organizer_id>'
    TIMEZONES = '/' + VERSION + '/data/timezones'
    RSVP = '/' + VERSION + '/rsvp'
    CODE = '/' + VERSION + '/code'
    # URL for Twitter authentication
    TWITTER_AUTH = '/' + VERSION + '/twitter-auth/<int:user_id>'
    TWITTER_CALLBACK = '/' + VERSION + '/twitter-callback/<int:user_id>'


class SocialNetworkApiUrl(object):
    """
    API relative URLs for social_network_service
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.SOCIAL_NETWORK_SERVICE_NAME, GTApis.SOCIAL_NETWORK_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    # TODO: Make this URL dynamic i.e different for staging, dev or prod
    UI_APP_URL = 'http://localhost:3000'
    EVENTS = HOST_NAME % ('/' + VERSION + '/events')
    EVENT = HOST_NAME % ('/' + VERSION + '/events/%s')
    SOCIAL_NETWORKS = HOST_NAME % ('/' + VERSION + '/social-networks')
    VENUES = HOST_NAME % ('/' + VERSION + '/venues')
    VENUE = HOST_NAME % ('/' + VERSION + '/venues/%s')
    EVENT_ORGANIZERS = HOST_NAME % ('/' + VERSION + '/event-organizers')
    EVENT_ORGANIZER = HOST_NAME % ('/' + VERSION + '/event-organizers/%s')
    TIMEZONES = HOST_NAME % ('/' + VERSION + '/data/timezones')
    MEETUP_GROUPS = HOST_NAME % ('/' + VERSION + '/social-networks/meetup-groups')
    TOKEN_VALIDITY = HOST_NAME % ('/' + VERSION + '/social-networks/%s/token/validity')
    TOKEN_REFRESH = HOST_NAME % ('/' + VERSION + '/social-networks/%s/token/refresh')
    USER_SOCIAL_NETWORK_CREDENTIALS = HOST_NAME % ('/' + VERSION + '/social-networks/%s/user/credentials')
    RSVP = HOST_NAME % ('/' + VERSION + '/rsvp')
    CODE = HOST_NAME % ('/' + VERSION + '/code')
    TWITTER_CALLBACK= HOST_NAME % ('/' + VERSION + '/twitter-callback/%s')


class SmsCampaignApi(object):
    """
    This class contains the REST endpoints of sms_campaign_service
    """
    VERSION = 'v1'
    # endpoint /v1/sms-campaigns
    # GET all campaigns of a user, POST new campaign, DELETE campaigns of a user from given ids
    CAMPAIGNS = '/' + VERSION + '/sms-campaigns'
    # endpoint /v1/sms-campaigns/:campaign_id
    # GET campaign by its id, POST: updates a campaign, DELETE a campaign from given id
    CAMPAIGN = '/' + VERSION + '/sms-campaigns/<int:campaign_id>'
    # /v1/sms-campaigns/:campaign_id/schedule
    # To schedule an SMS campaign
    SCHEDULE = '/' + VERSION + '/sms-campaigns/<int:campaign_id>/schedule'
    # endpoint /v1/sms-campaigns/:campaign_id/send
    # To send a campaign to candidates
    SEND = '/' + VERSION + '/sms-campaigns/<int:campaign_id>/send'
    # endpoint /v1/redirect/:id
    # This endpoint is hit when candidate clicks on any URL present in SMS body text.
    REDIRECT = '/' + VERSION + '/redirect/<int:url_conversion_id>'
    # endpoint /v1/receive
    # This endpoint is callback URL when candidate replies to a campaign via SMS
    RECEIVE = '/' + VERSION + '/receive'
    # endpoint /v1/sms-campaigns/:campaign_id/blasts
    # Gives the blasts of a campaign
    BLASTS = '/' + VERSION + '/sms-campaigns/<int:campaign_id>/blasts'
    # endpoint /v1/sms-campaigns/:campaign_id/blasts/:blast_id
    # Gives the blast object of SMS campaign from given blast id.
    BLAST = '/' + VERSION + '/sms-campaigns/<int:campaign_id>/blasts/<int:blast_id>'
    # endpoint /v1/sms-campaigns/:campaign_id/blasts/:blast_id/sends
    # Gives the sends objects of a blast object of SMS campaign from given blast id.
    BLAST_SENDS = '/' + VERSION + '/sms-campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends'
    # endpoint /v1/sms-campaigns/:campaign_id/blasts/:blast_id/replies
    # Gives the replies objects of a blast object of SMS campaign from given blast id.
    BLAST_REPLIES = '/' + VERSION + '/sms-campaigns/<int:campaign_id>/blasts/<int:blast_id>/replies'
    # endpoint /v1/sms-campaigns/:campaign_id/sends
    # This gives the records from "sends" for a given id of campaign
    SENDS = '/' + VERSION + '/sms-campaigns/<int:campaign_id>/sends'
    # endpoint /v1/sms-campaigns/:campaign_id/replies
    # This gives the records from "sms_campaign_reply" for a given id of campaign
    REPLIES = '/' + VERSION + '/sms-campaigns/<int:campaign_id>/replies'


class SmsCampaignApiUrl(object):
    """
    This class contains the REST URLs of sms_campaign_service
    """
    """ Endpoints' complete URLs for pyTests """
    VERSION = 'v1'
    # HOST_NAME is http://127.0.0.1:8012 for dev
    HOST_NAME = _get_host_name(GTApis.SMS_CAMPAIGN_SERVICE_NAME, GTApis.SMS_CAMPAIGN_SERVICE_PORT)
    CAMPAIGNS = HOST_NAME % ('/' + VERSION + '/sms-campaigns')
    CAMPAIGN = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s')
    SCHEDULE = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s/schedule')
    SEND = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s/send')
    REDIRECT = HOST_NAME % ('/' + VERSION + '/redirect/%s')
    RECEIVE = HOST_NAME % ('/' + VERSION + '/receive')
    BLASTS = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s/blasts')
    BLAST = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s/blasts/%s')
    SENDS = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s/sends')
    REPLIES = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s/replies')
    BLAST_SENDS = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s/blasts/%s/sends')
    BLAST_REPLIES = HOST_NAME % ('/' + VERSION + '/sms-campaigns/%s/blasts/%s/replies')


class PushCampaignApi(object):
    """
    REST URLs for Push Campaign Service endpoints
    """
    VERSION = 'v1'
    # endpoint /v1/push-campaigns
    # GET all campaigns of a user, POST new campaign, DELETE campaigns of a user from given ids
    CAMPAIGNS = '/' + VERSION + '/push-campaigns'
    # endpoint /v1/push-campaigns/:id
    # GET campaign by its id, POST: updates a campaign, DELETE a campaign from given id
    CAMPAIGN = '/' + VERSION + '/push-campaigns/<int:campaign_id>'
    # endpoint /v1/push-campaigns/:id/sends
    # This gives the records from "sends" for a given id of campaign
    SENDS = '/' + VERSION + '/push-campaigns/<int:campaign_id>/sends'
    BLASTS = '/' + VERSION + '/push-campaigns/<int:campaign_id>/blasts'
    BLAST = '/' + VERSION + '/push-campaigns/<int:campaign_id>/blasts/<int:blast_id>'
    BLAST_SENDS = '/' + VERSION + '/push-campaigns/<int:campaign_id>/blasts/<int:blast_id>/sends'
    # endpoint /v1/push-campaigns/:id/send
    # To send a campaign to candidates
    SEND = '/' + VERSION + '/push-campaigns/<int:campaign_id>/send'
    # /v1/push-campaigns/:id/schedule
    # To schedule a Push campaign
    SCHEDULE = '/' + VERSION + '/push-campaigns/<int:campaign_id>/schedule'
    # endpoint /v1/redirect/:id
    # This endpoint is hit when candidate clicks on any URL present in Push campaign's body text.
    REDIRECT = '/' + VERSION + '/redirect/<int:url_conversion_id>'

    # helper endpoints, need to get url_conversion records in some cases
    URL_CONVERSION = '/' + VERSION + '/url-conversions/<int:_id>'
    URL_CONVERSION_BY_SEND_ID = '/' + VERSION + '/send-url-conversions/<int:send_id>'


class PushCampaignApiUrl(object):
    """
    This class contains the REST URLs of push_campaign_service
    """
    VERSION = 'v1'
    """ Endpoints' complete URLs for pyTests """
    # HOST_NAME is http://127.0.0.1:8013 for dev
    HOST_NAME = _get_host_name(GTApis.PUSH_CAMPAIGN_SERVICE_NAME, GTApis.PUSH_CAMPAIGN_SERVICE_PORT)
    CAMPAIGNS = HOST_NAME % ('/' + VERSION + '/push-campaigns')
    CAMPAIGN = HOST_NAME % ('/' + VERSION + '/push-campaigns/%s')
    SENDS = HOST_NAME % ('/' + VERSION + '/push-campaigns/%s/sends')
    BLASTS = HOST_NAME % ('/' + VERSION + '/push-campaigns/%s/blasts')
    BLAST = HOST_NAME % ('/' + VERSION + '/push-campaigns/%s/blasts/%s')
    BLAST_SENDS = HOST_NAME % ('/' + VERSION + '/push-campaigns/%s/blasts/%s/sends')
    SEND = HOST_NAME % ('/' + VERSION + '/push-campaigns/%s/send')
    SCHEDULE = HOST_NAME % ('/' + VERSION + '/push-campaigns/%s/schedule')
    REDIRECT = HOST_NAME % ('/' + VERSION + '/redirect/%s')
    URL_CONVERSION = HOST_NAME % ('/' + VERSION + '/url-conversions/%s')
    URL_CONVERSION_BY_SEND_ID = HOST_NAME % ('/' + VERSION + '/send-url-conversions/%s')


class EmailCampaignApi(object):
    """
    REST URLs for Email Campaign Service endpoints
    """
    VERSION = 'v1'
    CAMPAIGNS = '/' + VERSION + '/email-campaigns'
    CAMPAIGN = '/' + VERSION + '/email-campaigns/<int:id>'
    # endpoint /v1/email-campaigns/:id/send
    # Send the campaign as specified by the id
    SEND = '/' + VERSION + '/email-campaigns/<int:campaign_id>/send'
    URL_REDIRECT = '/' + VERSION + '/redirect/<int:url_conversion_id>'
    # endpoint /v1/email-campaigns/:id/blasts
    # Gives the blasts of a campaign
    BLASTS = '/' + VERSION + '/email-campaigns/<int:campaign_id>/blasts'
    # endpoint /v1/email-campaigns/:id/blasts/:id
    # Gives the blast object of a campaign for a particular blast_id
    BLAST = '/' + VERSION + '/email-campaigns/<int:campaign_id>/blasts/<int:blast_id>'
    # endpoint /v1/email-campaigns/:id/sends
    # Gives the sends of a campaign
    SENDS = '/' + VERSION + '/email-campaigns/<int:campaign_id>/sends'
    # endpoint /v1/email-campaigns/:id/sends/:id
    # Gives the send object of a campaign for a particular send_id
    SEND_BY_ID = '/' + VERSION + '/email-campaigns/<int:campaign_id>/sends/<int:send_id>'


class EmailCampaignApiUrl(object):
    """
    This class contains URLs to be used in Py-tests
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.EMAIL_CAMPAIGN_SERVICE_NAME, GTApis.EMAIL_CAMPAIGN_SERVICE_PORT)
    CAMPAIGNS = HOST_NAME % ('/' + VERSION + '/email-campaigns')
    CAMPAIGN = HOST_NAME % ('/' + VERSION + '/email-campaigns/%s')
    SEND = HOST_NAME % ('/' + VERSION + '/email-campaigns/%s/send')
    URL_REDIRECT = HOST_NAME % ('/' + VERSION + '/redirect/%s')
    BLASTS = HOST_NAME % ('/' + VERSION + '/email-campaigns/%s/blasts')
    BLAST = HOST_NAME % ('/' + VERSION + '/email-campaigns/%s/blasts/%s')
    TEMPLATES = HOST_NAME % ('/' + VERSION + '/email-templates')
    TEMPLATES_FOLDER = HOST_NAME % ('/' + VERSION + '/email-template-folders')
    SENDS = HOST_NAME % ('/' + VERSION + '/email-campaigns/%s/sends')
    SEND_BY_ID = HOST_NAME % ('/' + VERSION + '/email-campaigns/%s/sends/%s')


class ATSServiceApi(object):
    """
    REST URLs for ATS service endpoints
    """
    VERSION = 'v1'
    ATS = '/' + VERSION + '/ats'
    ACCOUNT = '/' + VERSION + '/ats-accounts/<int:account_id>'
    ACCOUNTS = '/' + VERSION + '/ats-accounts'
    CANDIDATE = '/' + VERSION + '/ats-candidates/<int:candidate_id>/<int:ats_candidate_id>'
    CANDIDATES = '/' + VERSION + '/ats-candidates/<int:account_id>'
    CANDIDATES_REFRESH = '/' + VERSION + '/ats-candidates/refresh/<int:account_id>'


class ATSServiceApiUrl(object):
    """
    URLs for ATS services.
    """
    VERSION = 'v1'
    HOST_NAME = _get_host_name(GTApis.ATS_SERVICE_NAME, GTApis.ATS_SERVICE_PORT)
    HEALTH_CHECK = _get_health_check_url(HOST_NAME)
    ATS = HOST_NAME % ('/' + VERSION + '/ats')
    ACCOUNT = HOST_NAME % ('/' + VERSION  + '/ats-accounts/%s/%s')
    ACCOUNTS = HOST_NAME % ('/' + VERSION  + '/ats-accounts/%s')
    CANDIDATE = HOST_NAME % ('/' + VERSION + '/ats-candidates/%s/%s')
    CANDIDATES = HOST_NAME % ('/' + VERSION + '/ats-candidates/%s')
    CANDIDATES_REFRESH = HOST_NAME % ('/' + VERSION + '/ats-candidates/refresh/%s')
