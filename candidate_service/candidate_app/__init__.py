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
    CandidateResource, CandidateEmailCampaignResource, CandidateAddresses
)
api = GetTalentApi(app=app)

# Api resources
api.add_resource(
    CandidateResource,
    '/v1/candidates/<int:id>',
    '/v1/candidates/<email>',
    '/v1/candidates'
)

api.add_resource(
    CandidateAddresses,
    '/v1/candidates/<int:candidate_id>/addresses/<int:id>',
    endpoint='candidate_addresses'
)
api.add_resource(
    CandidateAddresses,
    '/v1/candidates/<int:candidate_id>/addresses',
    endpoint='candidate_addresses_2'
)

api.add_resource(CandidateEmailCampaignResource,
                 '/v1/candidates/<int:id>/email_campaigns/<int:email_campaign_id>/email_campaign_sends',
                 endpoint='candidates')

db.create_all()
db.session.commit()

logger.info('Starting candidate_service in %s environment',
            app.config['GT_ENVIRONMENT'])
