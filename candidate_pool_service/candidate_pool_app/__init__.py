__author__ = 'ufarooqi'

from flask import Flask
from candidate_pool_service.common.models.db import db
from candidate_pool_service.common import common_config
from healthcheck import HealthCheck
from candidate_pool_service.common.talent_api import TalentApi

app = Flask(__name__)
app.config.from_object(common_config)

logger = app.config['LOGGER']
from candidate_pool_service.common.error_handling import register_error_handlers
print "register error handlers"
register_error_handlers(app, logger)

db.init_app(app)
db.app = app

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from api.talent_pools import *
api = TalentApi(app=app)

api.add_resource(TalentPoolApi, '/talent-pools/<int:id>', '/talent-pools')
api.add_resource(TalentPoolGroupApi, '/groups/<int:group_id>/talent_pools')
api.add_resource(TalentPoolCandidateApi, '/talent-pools/<int:id>/candidates')

db.create_all()
db.session.commit()

logger.info("Starting candidate_pool_service in %s environment", app.config['GT_ENVIRONMENT'])