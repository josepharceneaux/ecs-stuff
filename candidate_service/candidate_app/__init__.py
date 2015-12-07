from flask import Flask
from candidate_service.common.models.db import db
from gt_custom_restful import *
from healthcheck import HealthCheck

app = Flask(__name__)
print "Running app: %s" % app

from candidate_service import config
app.config.from_object(config)

logger = app.config['LOGGER']

from candidate_service.common.error_handling import register_error_handlers
register_error_handlers(app=app, logger=logger)

db.init_app(app=app)
db.app = app

# Wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from candidate_service.candidate_app.api.v1_candidates import (
    CandidateResource, CandidateAddressResource, CandidateAreaOfInterestResource,
    CandidateEducationResource, CandidateEducationDegreeResource, CandidateEducationDegreeBulletResource,
    CandidateExperienceResource, CandidateExperienceBulletResource, CandidateWorkPreferenceResource,
    CandidateEmailResource, CandidatePhoneResource, CandidateMilitaryServiceResource,
    CandidatePreferredLocationResource
)
api = GetTalentApi(app=app)

# API RESOURCES
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

######################## CandidateExperience ########################
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

######################## CandidateExperienceBullet ########################
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

######################## CandidateEmail ########################
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

######################## CandidateMilitaryService ########################
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

######################## CandidatePhone ########################
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

######################## CandidatePreferredLocation ########################
api.add_resource(
    CandidatePreferredLocationResource,
    '/v1/candidates/<int:candidate_id>/preferred_locations',
    endpoint='candidate_preferred_locations_1'
)
api.add_resource(
    CandidatePreferredLocationResource,
    '/v1/candidates/<int:candidate_id>/preferred_locations/<int:id>',
    endpoint='candidate_preferred_locations_2'
)

######################## CandidateWorkPreference ########################
api.add_resource(
    CandidateWorkPreferenceResource,
    '/v1/candidates/<int:candidate_id>/work_preference/<int:id>',
    endpoint='candidate_work_preference'
)

# api.add_resource(CandidateEmailCampaignResource,
#                  '/v1/candidates/<int:id>/email_campaigns/<int:email_campaign_id>/email_campaign_sends',
#                  endpoint='candidates')

db.create_all()
db.session.commit()

logger.info('Starting candidate_service in %s environment', app.config['GT_ENVIRONMENT'])
