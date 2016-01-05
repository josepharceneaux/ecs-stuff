__author__ = 'ufarooqi'

from flask import request
from flask import current_app as app
from amazon_ses import send_email, DEFAULT_MAIL_SENDER
from ..talent_config_manager import ConfigKeys

ADMINS = ['osman@gettalent.com', 'vincent.mendolia@dice.com', 'ahmed@janim.me', 'jitesh.karesia@newvisionsoftware.in',
          'ashwin@gettalent.com', 'umar.farooqi.gt@gmail.com']


def email_error_to_admins(body, subject=""):
    email_admins(body, "Error", subject)


def email_notification_to_admins(body, subject=""):
    email_admins(body, "Notification", subject)


def email_admins(body, prefix, subject):

    env = app.config[ConfigKeys.ENV_KEY]
    # For development and circle ci do not send email notification to getTalent admins.
    if env == 'dev' or env == 'circle':
        return

    server_type = "Stage" if env == 'qa' else "Production"
    body = "%s\n\n\n\nRequest:\n%s" % (body, request)

    send_email(source=DEFAULT_MAIL_SENDER, subject="Talent Web %s %s: %s" % (server_type, prefix, subject), body=body,
               to_addresses=ADMINS)
