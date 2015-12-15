import os


class CandidateApiUrl:
    def __init__(self):
        pass

    env = os.environ.get('GT_ENVIRONMENT')

    if env == 'dev' or env == 'circle':
        CANDIDATE_SERVICE_HOST_NAME = 'http://127.0.0.1:8005/%s'
    elif env == 'qa':
        # TODO: Change this url after deployment
        CANDIDATE_SERVICE_HOST_NAME = 'http://127.0.0.1:8005/%s'
    elif env == 'prod':
        # TODO: Change this url after deployment
        CANDIDATE_SERVICE_HOST_NAME = 'http://127.0.0.1:8005/%s'
    else:
        raise Exception("Environment variable GT_ENVIRONMENT not set correctly - could not get environment")

    CANDIDATE = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates/%s"
    CANDIDATES = CANDIDATE_SERVICE_HOST_NAME % "v1/candidates"

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

