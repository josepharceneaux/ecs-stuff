from flask import Flask
from common.models.db import db

app = Flask(__name__)
app.config.from_object('candidate_service.config')

logger = app.config('LOGGER')

from common.error_handling import register_error_handlers
register_error_handlers(app=app, logger=logger)

db.init_app(app=app)
db.app = app

db.create_all()
db.session.commit()

logger.info('Starting candidate_service in %s environment',
            app.config['GT_ENVIRONMENT'])
