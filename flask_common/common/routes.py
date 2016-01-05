import os


class UserServiceApiUrl:
    def __init__(self):
        pass

    env = os.getenv('GT_ENVIRONMENT') or 'dev'

    if env == 'dev' or env == 'circle':
        USER_SERVICE_HOST_NAME = 'http://127.0.0.1:8004/v1/%s'
    elif env == 'qa':
        USER_SERVICE_HOST_NAME = 'https://user-service-staging.gettalent.com/v1/%s'
    elif env == 'prod':
        USER_SERVICE_HOST_NAME = 'https://user-service.gettalent.com/v1/%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not get environment")

    USERS_API = USER_SERVICE_HOST_NAME % 'users'
    DOMAINS_API = USER_SERVICE_HOST_NAME % 'domains'
    USER_ROLES_API = USER_SERVICE_HOST_NAME % 'users/%s/roles'
    DOMAIN_ROLES_API = USER_SERVICE_HOST_NAME % 'domain/%s/roles'
    DOMAIN_GROUPS_API = USER_SERVICE_HOST_NAME % 'domain/%s/groups'
    DOMAIN_GROUPS_UPDATE_API = USER_SERVICE_HOST_NAME % 'domain/groups/%s'
    USER_GROUPS_API = USER_SERVICE_HOST_NAME % 'groups/%s/users'
    UPDATE_PASSWORD_API = USER_SERVICE_HOST_NAME % 'users/update_password'
    FORGOT_PASSWORD_API = USER_SERVICE_HOST_NAME % 'users/forgot_password'
    RESET_PASSWORD_API = USER_SERVICE_HOST_NAME % 'users/reset_password/%s'


class AuthApiUrl:
    def __init__(self):
        pass

    env = os.getenv('GT_ENVIRONMENT') or 'dev'

    if env == 'dev' or env == 'circle':
        AUTH_SERVICE_HOST_NAME = 'http://127.0.0.1:8001/v1/%s'
    elif env == 'qa':
        AUTH_SERVICE_HOST_NAME = 'https://auth-service-staging.gettalent.com/v1/%s'
    elif env == 'prod':
        AUTH_SERVICE_HOST_NAME = 'https://auth-service.gettalent.com/v1/%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not get environment")

    AUTH_SERVICE_TOKEN_CREATE_URI = AUTH_SERVICE_HOST_NAME % 'oauth2/token'
    AUTH_SERVICE_TOKEN_REVOKE_URI = AUTH_SERVICE_HOST_NAME % 'oauth2/revoke'
    AUTH_SERVICE_AUTHORIZE_URI = AUTH_SERVICE_HOST_NAME % 'oauth2/authorize'


class CandidateApiUrl:
    def __init__(self):
        pass

    env = os.getenv('GT_ENVIRONMENT') or 'dev'

    if env == 'dev' or env == 'circle':
        CANDIDATE_SERVICE_HOST_NAME = 'http://127.0.0.1:8005/%s'
    elif env == 'qa':
        CANDIDATE_SERVICE_HOST_NAME = 'https://candidate-service-staging.gettalent.com/%s'
    elif env == 'prod':
        CANDIDATE_SERVICE_HOST_NAME = 'https://candidate-service.gettalent.com/%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not get environment")

    CANDIDATE = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s"
    CANDIDATES = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates"

    CANDIDATE_SEARCH_URI = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/search"

    CANDIDATES_DOCUMENTS_URI = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/documents"

    ADDRESS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/addresses/%s"
    ADDRESSES = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/addresses"

    AOI = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/areas_of_interest/%s"
    AOIS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/areas_of_interest"

    CUSTOM_FIELD = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/custom_fields/%s"
    CUSTOM_FIELDS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/custom_fields"

    EDUCATION = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/educations/%s"
    EDUCATIONS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/educations"

    DEGREE = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/educations/%s/degrees/%s"
    DEGREES = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/educations/%s/degrees"

    DEGREE_BULLET = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/educations/%s/degrees/%s/bullets/%s"
    DEGREE_BULLETS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/educations/%s/degrees/%s/bullets"

    EMAIL = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/emails/%s"
    EMAILS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/emails"

    EXPERIENCE = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/experiences/%s"
    EXPERIENCES = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/experiences"

    EXPERIENCE_BULLET = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/experiences/%s/bullets/%s"
    EXPERIENCE_BULLETS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/experiences/%s/bullets"

    MILITARY_SERVICE = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/military_services/%s"
    MILITARY_SERVICES = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/military_services"

    PHONE = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/phones/%s"
    PHONES = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/phones"

    PREFERRED_LOCATION = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/preferred_locations/%s"
    PREFERRED_LOCATIONS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/preferred_locations"

    SKILL = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/skills/%s"
    SKILLS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/skills"

    SOCIAL_NETWORK = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/social_networks/%s"
    SOCIAL_NETWORKS = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/social_networks"

    WORK_PREFERENCE = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/work_preference/%s"

    CANDIDATE_EDIT = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s/edits"


class SchedulerApiUrl:
    def __init__(self):
        pass

    env = os.getenv('GT_ENVIRONMENT') or 'dev'

    if env == 'dev' or env == 'circle':
        SCHEDULER_SERVICE_HOST_NAME = 'http://127.0.0.1:8011/%s'
    elif env == 'qa':
        SCHEDULER_SERVICE_HOST_NAME = 'https://scheduler-service-staging.gettalent.com/%s'
    elif env == 'prod':
        SCHEDULER_SERVICE_HOST_NAME = 'https://scheduler-service.gettalent.com/%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not get environment")

    TASKS = SCHEDULER_SERVICE_HOST_NAME % "tasks/"
    SINGLE_TASK = SCHEDULER_SERVICE_HOST_NAME % 'tasks/id/%s'


class CandidatePoolApiUrl:
    def __init__(self):
        pass

    env = os.getenv('GT_ENVIRONMENT') or 'dev'

    if env == 'dev' or env == 'circle':
        CANDIDATE_POOL_SERVICE_HOST_NAME = 'http://127.0.0.1:8008/v1/%s'
    elif env == 'qa':
        CANDIDATE_POOL_SERVICE_HOST_NAME = 'https://candidate-pool-service-staging.gettalent.com/v1/%s'
    elif env == 'prod':
        CANDIDATE_POOL_SERVICE_HOST_NAME = 'https://candidate-pool-service.gettalent.com/v1/%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not get environment")

    TALENT_POOL_STATS = CANDIDATE_POOL_SERVICE_HOST_NAME % "talent-pools/stats"
    TALENT_POOL_GET_STATS = CANDIDATE_POOL_SERVICE_HOST_NAME % "talent-pool/%s/stats"
    TALENT_PIPELINE_STATS = CANDIDATE_POOL_SERVICE_HOST_NAME % "talent-pipelines/stats"
    TALENT_PIPELINE_GET_STATS = CANDIDATE_POOL_SERVICE_HOST_NAME % "talent-pipeline/%s/stats"


class SpreadsheetImportApiUrl:
    def __init__(self):
        pass

    env = os.getenv('GT_ENVIRONMENT') or 'dev'

    if env == 'dev' or env == 'circle':
        SPREADSHEET_IMPORT_SERVICE_HOST_NAME = 'http://127.0.0.1:8009/v1/parse_spreadsheet/%s'
    elif env == 'qa':
        SPREADSHEET_IMPORT_SERVICE_HOST_NAME = \
            'https://spreadsheet-import-service-staging.gettalent.com/v1/parse_spreadsheet/%s'
    elif env == 'prod':
        SPREADSHEET_IMPORT_SERVICE_HOST_NAME = \
            'https://spreadsheet-import-service.gettalent.com/v1/parse_spreadsheet/%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not get environment")

    CONVERT_TO_TABLE = SPREADSHEET_IMPORT_SERVICE_HOST_NAME % "convert_to_table"
    IMPORT_CANDIDATES = SPREADSHEET_IMPORT_SERVICE_HOST_NAME % 'import_candidates'
