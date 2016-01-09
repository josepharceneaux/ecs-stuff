from flask import Flask
from flask.ext.cors import CORS
from candidate_service.common.talent_config_manager import load_gettalent_config, TalentConfigKeys
from candidate_service.common.routes import CandidateApi, HEALTH_CHECK

app = Flask(__name__)
load_gettalent_config(app.config)

logger = app.config[TalentConfigKeys.LOGGER]

try:
    from candidate_service.common.error_handling import register_error_handlers
    register_error_handlers(app=app, logger=logger)

    from candidate_service.common.models.db import db
    db.init_app(app=app)
    db.app = app

    from candidate_service.common.redis_cache import redis_store
    redis_store.init_app(app)

    # Wrap the flask app and give a healthcheck url
    from healthcheck import HealthCheck
    health = HealthCheck(app, HEALTH_CHECK)

    from candidate_service.candidate_app.api.v1_candidates import (
        CandidateResource, CandidateAddressResource, CandidateAreaOfInterestResource,
        CandidateEducationResource, CandidateEducationDegreeResource, CandidateEducationDegreeBulletResource,
        CandidateExperienceResource, CandidateExperienceBulletResource, CandidateWorkPreferenceResource,
        CandidateEmailResource, CandidatePhoneResource, CandidateMilitaryServiceResource,
        CandidatePreferredLocationResource, CandidateSkillResource, CandidateSocialNetworkResource,
        CandidateCustomFieldResource, CandidateEditResource, CandidatesResource, CandidateOpenWebResource,
        CandidateViewResource
    )
    from candidate_service.candidate_app.api.candidate_search_api import CandidateSearch, CandidateDocuments

    from candidate_service.common.talent_api import TalentApi
    api = TalentApi(app=app)
    # Enable CORS
    CORS(app, resources={
        r'%s/*' % CandidateApi.CANDIDATES: {
            'origins': '*',
            'allow_headers': ['Content-Type', 'Authorization']
        }
    })
    # API RESOURCES
    ######################## CandidateResource ########################
    api.add_resource(
        CandidateResource,
        CandidateApi.CANDIDATE_ID,
        CandidateApi.CANDIDATE_EMAIL,
        endpoint='candidate_resource'
    )

    ######################## CandidatesResource ########################
    api.add_resource(
        CandidatesResource,
        CandidateApi.CANDIDATES,
        endpoint='candidates_resource'
    )

    ######################## CandidateAddressResource ########################
    api.add_resource(
        CandidateAddressResource,
        CandidateApi.ADDRESSES,
        endpoint='candidate_address_1'
    )
    api.add_resource(
        CandidateAddressResource,
        CandidateApi.ADDRESS,
        endpoint='candidate_address_2'
    )

    ######################## CandidateAreaOfInterestResource ########################
    api.add_resource(
        CandidateAreaOfInterestResource,
        CandidateApi.AOIS,
        endpoint='candidate_area_of_interest_1'
    )
    api.add_resource(
        CandidateAreaOfInterestResource,
        CandidateApi.AOI,
        endpoint='candidate_area_of_interest_2'
    )

    ######################## CandidateCustomFieldResource ########################
    api.add_resource(
        CandidateCustomFieldResource,
        CandidateApi.CUSTOM_FIELDS,
        endpoint='candidate_custom_field_1'
    )
    api.add_resource(
        CandidateCustomFieldResource,
        CandidateApi.CUSTOM_FIELD,
        endpoint='candidate_custom_field_2'
    )

    ######################## CandidateEducationResource ########################
    api.add_resource(
        CandidateEducationResource,
        CandidateApi.EDUCATIONS,
        endpoint='candidate_education_1'
    )
    api.add_resource(
        CandidateEducationResource,
        CandidateApi.EDUCATION,
        endpoint='candidate_education_2'
    )

    ######################## CandidateEducationDegreeResource ########################
    api.add_resource(
        CandidateEducationDegreeResource,
        CandidateApi.DEGREES,
        endpoint='candidate_education_degree_1'
    )
    api.add_resource(
        CandidateEducationDegreeResource,
        CandidateApi.DEGREE,
        endpoint='candidate_education_degree_2'
    )

    ######################## CandidateEducationDegreeBulletResource ########################
    api.add_resource(
        CandidateEducationDegreeBulletResource,
        CandidateApi.DEGREE_BULLETS,
        endpoint='candidate_education_degree_bullet_1'
    )
    api.add_resource(
        CandidateEducationDegreeBulletResource,
        CandidateApi.DEGREE_BULLET,
        endpoint='candidate_education_degree_bullet_2'
    )

    ######################## CandidateExperienceResource ########################
    api.add_resource(
        CandidateExperienceResource,
        CandidateApi.EXPERIENCES,
        endpoint='candidate_experience_1'
    )
    api.add_resource(
        CandidateExperienceResource,
        CandidateApi.EXPERIENCE,
        endpoint='candidate_experience_2'
    )

    ######################## CandidateExperienceBulletResource ########################
    api.add_resource(
        CandidateExperienceBulletResource,
        CandidateApi.EXPERIENCE_BULLETS,
        endpoint='candidate_experience_bullet_1'
    )
    api.add_resource(
        CandidateExperienceBulletResource,
        CandidateApi.EXPERIENCE_BULLET,
        endpoint='candidate_experience_bullet_2'
    )

    ######################## CandidateEmailResource ########################
    api.add_resource(
        CandidateEmailResource,
        CandidateApi.EMAILS,
        endpoint='candidate_email_1'
    )
    api.add_resource(
        CandidateEmailResource,
        CandidateApi.EMAIL,
        endpoint='candidate_email_2'
    )

    ######################## CandidateMilitaryServiceResource ########################
    api.add_resource(
        CandidateMilitaryServiceResource,
        CandidateApi.MILITARY_SERVICES,
        endpoint='candidate_military_service_1'
    )
    api.add_resource(
        CandidateMilitaryServiceResource,
        CandidateApi.MILITARY_SERVICE,
        endpoint='candidate_military_service_2'
    )

    ######################## CandidatePhoneResource ########################
    api.add_resource(
        CandidatePhoneResource,
        CandidateApi.PHONES,
        endpoint='candidate_phone_1'
    )
    api.add_resource(
        CandidatePhoneResource,
        CandidateApi.PHONE,
        endpoint='candidate_phone_2'
    )

    ######################## CandidatePreferredLocationResource ########################
    api.add_resource(
        CandidatePreferredLocationResource,
        CandidateApi.PREFERRED_LOCATIONS,
        endpoint='candidate_preferred_location_1'
    )
    api.add_resource(
        CandidatePreferredLocationResource,
        CandidateApi.PREFERRED_LOCATION,
        endpoint='candidate_preferred_location_2'
    )

    ######################## CandidateSkillResource ########################
    api.add_resource(
        CandidateSkillResource,
        CandidateApi.SKILLS,
        endpoint='candidate_skill_1'
    )
    api.add_resource(
        CandidateSkillResource,
        CandidateApi.SKILL,
        endpoint='candidate_skill_2'
    )

    ######################## CandidateSocialNetworkResource ########################
    api.add_resource(
        CandidateSocialNetworkResource,
        CandidateApi.SOCIAL_NETWORKS,
        endpoint='candidate_social_networks_1'
    )
    api.add_resource(
        CandidateSocialNetworkResource,
        CandidateApi.SOCIAL_NETWORK,
        endpoint='candidate_social_networks_2'
    )

    ######################## CandidateWorkPreferenceResource ########################
    api.add_resource(
        CandidateWorkPreferenceResource,
        '/v1/candidates/<int:candidate_id>/work_preference/<int:id>',
        endpoint='candidate_work_preference'
    )

    ######################## CandidateEditResource ########################
    api.add_resource(
        CandidateEditResource,
        '/v1/candidates/<int:id>/edits',
        endpoint='candidate_edit'
    )

    ######################## CandidateViewResource ########################
    api.add_resource(CandidateViewResource,
                     '/v1/candidates/<int:id>/views',
                     endpoint='candidate_views')

    # ****** Candidate Search *******
    api.add_resource(CandidateSearch, CandidateApi.CANDIDATE_SEARCH)

    # ****** Candidate Documents *******
    api.add_resource(CandidateDocuments, CandidateApi.CANDIDATES_DOCUMENTS)

    # ****** OPENWEB Request *******
    api.add_resource(CandidateOpenWebResource, CandidateApi.OPENWEB, endpoint='openweb')

    db.create_all()
    db.session.commit()

    logger.info('Starting candidate_service in %s environment', app.config[TalentConfigKeys.ENV_KEY])

except Exception as e:
    logger.exception("Couldn't start candidate_service in %s environment because: %s"
                     % (app.config[TalentConfigKeys.ENV_KEY], e.message))
