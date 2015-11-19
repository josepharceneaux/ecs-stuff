from email_campaign.common.celery import celery_app

from email_campaign.common.models.email_marketing import EmailCampaign
from email_campaign.common.models.user import User
__author__ = 'jitesh'


@celery_app.task
def add(x, y):
    return x + y


@celery_app.task
def send_scheduled_campaign(*args, **kwargs):
    """Watch dog to check if any campaign is to be send now
    If there is any campaign it sends the email
    """
    emails_sent = 0
    try:
        logger.info("Running schedule campaigning vars= %s", kwargs)
        campaign = EmailCampaign.query.filter_by(kwargs.get('campaign_id')).all()
        user = User.query.filter_by(kwargs.get('user_id')).first()
        email_client_id = kwargs.get('email_client_id')
        emails_sent = send_emails_to_campaign(campaign=campaign, user=user,
                                              email_client_id=email_client_id)
    except Exception:
        logger.exception("Received exception sending scheduled email campaign. Input vars: %s", kwargs)

        from ..common.errors import  email_error_to_admins

        email_error_to_admins("input vars: %s" % kwargs,
                              "Error sending email campaign") #some implementation is left


    db.session.commit()
    return emails_sent


