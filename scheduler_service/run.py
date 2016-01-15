"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
# Initializing App. This line should come before any imports from models
import os

from scheduler_service import init_app
from scheduler_service.common.routes import GTApis

app, celery = init_app()


# Split the scheduler from celery, so that celery worker can start from terminal
# Celery tasks needs name of included file. If the import is above the file, celery will not recognize
# updated file. So, it should be specific to app only
def scheduler_app():
    from scheduler_service.api.scheduler_api import scheduler_blueprint
    # Run Celery from terminal as
    # celery -A scheduler_service.app.app.celery worker
    app.register_blueprint(scheduler_blueprint)
    from scheduler_service.scheduler import scheduler
    # Start scheduler before starting flask app
    scheduler.start()

if __name__ == '__main__':
    scheduler_app()
    app.run(host='0.0.0.0', port=GTApis.SCHEDULER_SERVICE_PORT, debug=False)

