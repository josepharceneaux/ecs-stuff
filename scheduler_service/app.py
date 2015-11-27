"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
# Initializing App. This line should come before any imports from models
from scheduler_service import init_app
from scheduler_service.scheduler import scheduler

app = init_app()

from scheduler_service.api.scheduler_api import scheduler_blueprint


# Run Celery from terminal as
# celery -A scheduler_service.app.app.celery worker

# Third party imports


app.register_blueprint(scheduler_blueprint)

scheduler.start()

if __name__ == '__main__':
    app.run(port=8009)


