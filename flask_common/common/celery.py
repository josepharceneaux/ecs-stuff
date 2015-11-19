""" Script runs as separate process with celery command
 Usage: open terminal cd to talent-flask-services directory
 Run the following command to start celery worker:
    $ celery -A common worker --loglevel=info
"""
from __future__ import absolute_import

from celery import Celery
import os

# For now hardcoding it because this script needs to be run as celery command from terminal.
os.environ['GT_ENVIRONMENT'] = 'dev'  # TODO

from email_campaign.common.common_config import BROKER_URL


__author__ = 'jitesh'

celery_app = Celery('talent-flask-services', broker=BROKER_URL,
                    include=['email_campaign.modules.tasks'])

if __name__ == '__main__':
    celery_app.start()
