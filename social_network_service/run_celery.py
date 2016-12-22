"""
    Run Celery Worker

For Celery to run from command line, script runs as separate process with celery command

 Usage: open terminal cd to talent-flask-services directory

 Run the following command to start celery worker:

    $ celery -A social_network_service.social_network_app.celery_app worker --concurrency=4 --loglevel=info
"""

# Service Specific
from social_network_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs
from social_network_service.modules.constants import QUEUE_NAME
from social_network_service.common.talent_celery import CELERY_WORKER_ARGS
from social_network_service.social_network_app import celery_app, app
from social_network_service.tasks import import_meetup_events

if app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV]:
    # Run importer task for dev environment
    import_meetup_events.delay()
celery_app.start(argv=CELERY_WORKER_ARGS + [QUEUE_NAME])
