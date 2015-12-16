from flask import Flask
from candidate_service.common.models.db import db
from gt_custom_restful import *
from healthcheck import HealthCheck

app = Flask(__name__)
print "Running app: %s" % app

from candidate_service.common import common_config
app.config.from_object(common_config)

logger = app.config['LOGGER']

from candidate_service.common.error_handling import register_error_handlers
register_error_handlers(app=app, logger=logger)

db.init_app(app=app)
db.app = app

# Wrap the flask app and give a healthcheck url
health = HealthCheck(app, "/healthcheck")

from candidate_service.candidate_app.api.v1_candidates import (
    CandidateResource, CandidateAddressResource, CandidateAreaOfInterestResource,
    CandidateEducationResource, CandidateEducationDegreeResource, CandidateEducationDegreeBulletResource,
    CandidateExperienceResource, CandidateExperienceBulletResource, CandidateWorkPreferenceResource,
    CandidateEmailResource, CandidatePhoneResource, CandidateMilitaryServiceResource,
    CandidatePreferredLocationResource, CandidateSkillResource, CandidateSocialNetworkResource,
    CandidateCustomFieldResource, CandidateEditResource
)
from candidate_service.candidate_app.api.candidate_search_api import CandidateSearch

api = GetTalentApi(app=app)

# API RESOURCES
######################## CandidateResource ########################
api.add_resource(
    CandidateResource,
    '/v1/candidates/<int:id>',
    '/v1/candidates/<email>',
    '/v1/candidates',
    endpoint='candidate_resource'
)

######################## CandidateAddressResource ########################
api.add_resource(
    CandidateAddressResource,
    '/v1/candidates/<int:candidate_id>/addresses',
    endpoint='candidate_address_1'
)
api.add_resource(
    CandidateAddressResource,
    '/v1/candidates/<int:candidate_id>/addresses/<int:id>',
    endpoint='candidate_address_2'
)

######################## CandidateAreaOfInterestResource ########################
api.add_resource(
    CandidateAreaOfInterestResource,
    '/v1/candidates/<int:candidate_id>/areas_of_interest',
    endpoint='candidate_area_of_interest_1'
)
api.add_resource(
    CandidateAreaOfInterestResource,
    '/v1/candidates/<int:candidate_id>/areas_of_interest/<int:id>',
    endpoint='candidate_area_of_interest_2'
)

######################## CandidateCustomFieldResource ########################
api.add_resource(
    CandidateCustomFieldResource,
    '/v1/candidates/<int:candidate_id>/custom_fields',
    endpoint='candidate_custom_field_1'
)
api.add_resource(
    CandidateCustomFieldResource,
    '/v1/candidates/<int:candidate_id>/custom_fields/<int:id>',
    endpoint='candidate_custom_field_2'
)

######################## CandidateEducationResource ########################
api.add_resource(
    CandidateEducationResource,
    '/v1/candidates/<int:candidate_id>/educations',
    endpoint='candidate_education_1'
)
api.add_resource(
    CandidateEducationResource,
    '/v1/candidates/<int:candidate_id>/educations/<int:id>',
    endpoint='candidate_education_2'
)

######################## CandidateEducationDegreeResource ########################
api.add_resource(
    CandidateEducationDegreeResource,
    '/v1/candidates/<int:candidate_id>/educations/<int:education_id>/degrees',
    endpoint='candidate_education_degree_1'
)
api.add_resource(
    CandidateEducationDegreeResource,
    '/v1/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:id>',
    endpoint='candidate_education_degree_2'
)

######################## CandidateEducationDegreeBulletResource ########################
api.add_resource(
    CandidateEducationDegreeBulletResource,
    '/v1/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:degree_id>/bullets',
    endpoint='candidate_education_degree_bullet_1'
)
api.add_resource(
    CandidateEducationDegreeBulletResource,
    '/v1/candidates/<int:candidate_id>/educations/<int:education_id>/degrees/<int:degree_id>/bullets/<int:id>',
    endpoint='candidate_education_degree_bullet_2'
)

######################## CandidateExperienceResource ########################
api.add_resource(
    CandidateExperienceResource,
    '/v1/candidates/<int:candidate_id>/experiences',
    endpoint='candidate_experience_1'
)
api.add_resource(
    CandidateExperienceResource,
    '/v1/candidates/<int:candidate_id>/experiences/<int:id>',
    endpoint='candidate_experience_2'
)

######################## CandidateExperienceBulletResource ########################
api.add_resource(
    CandidateExperienceBulletResource,
    '/v1/candidates/<int:candidate_id>/experiences/<int:experience_id>/bullets',
    endpoint='candidate_experience_bullet_1'
)
api.add_resource(
    CandidateExperienceBulletResource,
    '/v1/candidates/<int:candidate_id>/experiences/<int:experience_id>/bullets/<int:id>',
    endpoint='candidate_experience_bullet_2'
)

######################## CandidateEmailResource ########################
api.add_resource(
    CandidateEmailResource,
    '/v1/candidates/<int:candidate_id>/emails',
    endpoint='candidate_email_1'
)
api.add_resource(
    CandidateEmailResource,
    '/v1/candidates/<int:candidate_id>/emails/<int:id>',
    endpoint='candidate_email_2'
)

######################## CandidateMilitaryServiceResource ########################
api.add_resource(
    CandidateMilitaryServiceResource,
    '/v1/candidates/<int:candidate_id>/military_services',
    endpoint='candidate_military_service_1'
)
api.add_resource(
    CandidateMilitaryServiceResource,
    '/v1/candidates/<int:candidate_id>/military_services/<int:id>',
    endpoint='candidate_military_service_2'
)

######################## CandidatePhoneResource ########################
api.add_resource(
    CandidatePhoneResource,
    '/v1/candidates/<int:candidate_id>/phones',
    endpoint='candidate_phone_1'
)
api.add_resource(
    CandidatePhoneResource,
    '/v1/candidates/<int:candidate_id>/phones/<int:id>',
    endpoint='candidate_phone_2'
)

######################## CandidatePreferredLocationResource ########################
api.add_resource(
    CandidatePreferredLocationResource,
    '/v1/candidates/<int:candidate_id>/preferred_locations',
    endpoint='candidate_preferred_location_1'
)
api.add_resource(
    CandidatePreferredLocationResource,
    '/v1/candidates/<int:candidate_id>/preferred_locations/<int:id>',
    endpoint='candidate_preferred_location_2'
)

######################## CandidateSkillResource ########################
api.add_resource(
    CandidateSkillResource,
    '/v1/candidates/<int:candidate_id>/skills',
    endpoint='candidate_skill_1'
)
api.add_resource(
    CandidateSkillResource,
    '/v1/candidates/<int:candidate_id>/skills/<int:id>',
    endpoint='candidate_skill_2'
)

######################## CandidateSocialNetworkResource ########################
api.add_resource(
    CandidateSocialNetworkResource,
    '/v1/candidates/<int:candidate_id>/social_networks',
    endpoint='candidate_social_networks_1'
)
api.add_resource(
    CandidateSocialNetworkResource,
    '/v1/candidates/<int:candidate_id>/social_networks/<int:id>',
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

######################## CandidateEmailCampaignResource ########################
# api.add_resource(CandidateEmailCampaignResource,
#                  '/v1/candidates/<int:id>/email_campaigns/<int:email_campaign_id>/email_campaign_sends',
#                  endpoint='candidates')

# ****** Candidate Search *******
api.add_resource(CandidateSearch,
                 '/v1/candidates/search')

db.create_all()
db.session.commit()

logger.info('Starting candidate_service in %s environment', app.config['GT_ENVIRONMENT'])
