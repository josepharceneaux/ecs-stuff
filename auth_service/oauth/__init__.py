__author__ = 'ufarooqi'

from flask import Flask
from flask_oauthlib.provider import OAuth2Provider

from auth_service.common.models.db import db
from auth_service import config

app = Flask(__name__)
app.config.from_object(config)

logger = app.config['LOGGER']
from auth_service.common.error_handling import register_error_handlers
print "register error handlers"
register_error_handlers(app, logger)

db.init_app(app)
db.app = app

gt_oauth = OAuth2Provider()
gt_oauth.init_app(app)

from oauth_utilities import GetTalentOauthValidator
gt_oauth._validator = GetTalentOauthValidator()

import views

db.create_all()
db.session.commit()

logger.info("Starting auth_service in %s environment", app.config['GT_ENVIRONMENT'])
