from email_campaign.common.celery import celery_app

__author__ = 'jitesh'


@celery_app.task
def add(x, y):
    return x + y


@celery_app.task
def send_scheduled_campaign():
    """Watch dog to check if any campaign is to be send now
    If there is any campaign it sends the email
    """
    pass

