"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
# Initializing App. This line should come before any imports from models
import os

from scheduler_service import init_app

app, celery = init_app()


# Split the scheduler from celery, so that celery worker can start from terminal
def scheduler_app():
    from scheduler_service.api.scheduler_api import scheduler_blueprint
    # Run Celery from terminal as
    # celery -A scheduler_service.app.app.celery worker
    app.register_blueprint(scheduler_blueprint)
    from scheduler_service.scheduler import scheduler
    # Start scheduler before starting flask app
    scheduler.start()

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    scheduler_app()
    app.run(host='0.0.0.0', port=8009, debug=False)


