from flask import Flask
from views import api
from common.models.db import db
from common.error_handling import register_error_handlers

__author__ = 'jitesh'

app = Flask(__name__)
app.config.from_object('common.talent_config')

app.register_blueprint(api.mod)

logger = app.config['LOGGER']

db.init_app(app)
db.app = app

register_error_handlers(app, logger)

logger.info("Starting email_campaign_service in %s environment", app.config['GT_ENVIRONMENT'])

