"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
# Initializing App. This line should come before any imports from models
import os

from scheduler_service import celery_app as celery, flask_app as app
from scheduler_service.common.routes import GTApis


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    # Start APSscheduler
    from scheduler_service.scheduler import scheduler
    scheduler.start()
    app.run(host='0.0.0.0', port=GTApis.SCHEDULER_SERVICE_PORT, debug=False)

