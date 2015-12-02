from flask import Flask
from candidate_service.common.models.db import db
from healthcheck import HealthCheck
from candidate_service.common.talent_api import TalentApi
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
    CandidateResource, CandidateEmailCampaignResource
)
from candidate_service.candidate_app.api.smartlists_api import SmartlistCandidates, SmartlistResource

api = TalentApi(app=app)
api.add_resource(CandidateResource,
                 '/v1/candidates/<int:id>',
                 '/v1/candidates/<email>',
                 '/v1/candidates')
api.add_resource(CandidateEmailCampaignResource,
                 '/v1/candidates/<int:id>/email_campaigns/<int:email_campaign_id>/email_campaign_sends',
                 endpoint='candidates')

api.add_resource(SmartlistResource,
                 '/v1/smartlists/<int:id>',  # GET
                 '/v1/smartlists')           # POST (create smartlist)

api.add_resource(SmartlistCandidates,
                 '/v1/smartlists/<int:smartlist_id>/candidates')

db.create_all()
db.session.commit()

logger.info('Starting candidate_service in %s environment',
            app.config['GT_ENVIRONMENT'])
