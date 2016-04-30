"""
    This module contains flask app startup.
    We register blueprints for different APIs with this app.
    Error handlers are added at the end of file.
"""
# Standard  Library imports
# Initializing App. This line should come before any imports from models

from scheduler_service import flask_app as app
from scheduler_service.common.routes import GTApis


if __name__ == '__main__':
    from migrate_jobs import migrate_sched_jobs
    migrate_sched_jobs()
    app.run(host='0.0.0.0', port=GTApis.SCHEDULER_SERVICE_PORT, use_reloader=True, debug=False, threaded=True)

