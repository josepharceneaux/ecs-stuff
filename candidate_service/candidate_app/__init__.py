from flask import Flask
from common.models.db import db
from gt_custom_restful import *


app = Flask(__name__)
print "Running app: %s" % app
import config
app.config.from_object('candidate_service.config')

logger = app.config['LOGGER']

from common.error_handling import register_error_handlers
register_error_handlers(app=app, logger=logger)

db.init_app(app=app)
db.app = app

from candidate_service.candidate_app.api.v1_candidates import (
    CandidateResource, CandidateEmailCampaignResource
)
api = GetTalentApi(app=app)
api.add_resource(CandidateResource,
                 '/v1/candidates/<int:id>',
                 '/v1/candidates/<email>',
                 '/v1/candidates')
api.add_resource(CandidateEmailCampaignResource,
                 '/v1/candidates/<int:id>/email_campaigns/<int:email_campaign_id>/email_campaign_sends', endpoint='candidates')

db.create_all()
db.session.commit()

logger.info('Starting candidate_service in %s environment',
            app.config['GT_ENVIRONMENT'])