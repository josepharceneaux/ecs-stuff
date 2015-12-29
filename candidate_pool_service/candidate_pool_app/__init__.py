__author__ = 'ufarooqi'

from flask import Flask
from candidate_pool_service.common.models.db import db
from candidate_pool_service.common.redis_cache import redis_store
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

# Initialize Redis Cache
redis_store.init_app(app)

# wrap the flask app and give a heathcheck url
health = HealthCheck(app, "/healthcheck")

from api.talent_pools import *
from api.talent_pipelines import *

api = TalentApi(app=app)

api.add_resource(TalentPoolApi, '/talent-pools/<int:id>', '/talent-pools')
api.add_resource(TalentPoolGroupApi, '/groups/<int:group_id>/talent_pools')
api.add_resource(TalentPoolCandidateApi, '/talent-pools/<int:id>/candidates')
api.add_resource(TalentPipelineApi, '/talent-pipelines/<int:id>', '/talent-pipelines')
api.add_resource(TalentPipelineSmartListApi, '/talent-pipeline/<int:id>/smart_lists')
api.add_resource(TalentPipelineCandidates, '/talent-pipeline/<int:id>/candidates')

db.create_all()
db.session.commit()

from candidate_pool_service.candidate_pool_app.talent_pools_pipelines_utilities import \
    schedule_talent_pool_and_pipelines_daily_stats_update

schedule_talent_pool_and_pipelines_daily_stats_update()

logger.info("Starting candidate_pool_service in %s environment", app.config['GT_ENVIRONMENT'])