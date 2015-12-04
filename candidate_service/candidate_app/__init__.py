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

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from candidate_service.candidate_app.api.v1_candidates import (
    CandidateResource, CandidateAddressResource, CandidateAreaOfInterestResource,
    CandidateEducationResource, CandidateEducationDegreeResource
)
api = GetTalentApi(app=app)

# Api resources
api.add_resource(
    CandidateResource,
    '/v1/candidates/<int:id>',
    '/v1/candidates/<email>',
    '/v1/candidates'
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

# api.add_resource(CandidateEmailCampaignResource,
#                  '/v1/candidates/<int:id>/email_campaigns/<int:email_campaign_id>/email_campaign_sends',
#                  endpoint='candidates')

db.create_all()
db.session.commit()

logger.info('Starting candidate_service in %s environment', app.config['GT_ENVIRONMENT'])
