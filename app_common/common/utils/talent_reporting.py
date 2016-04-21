__author__ = 'ufarooqi'

from flask import request
from flask import current_app as app
from amazon_ses import send_email, get_default_email_info
from ..talent_config_manager import TalentConfigKeys

ADMINS = ['osman@gettalent.com', 'vincent.mendolia@dice.com', 'ahmed@janim.me', 'jitesh.karesia@newvisionsoftware.in',
          'ashwin@gettalent.com', 'umar.farooqi.gt@gmail.com']


def email_error_to_admins(body, subject=""):
    email_admins(body, "Error", subject)


def email_notification_to_admins(body, subject=""):
    email_admins(body, "Notification", subject)


def email_admins(body, prefix, subject):

    env = app.config[TalentConfigKeys.ENV_KEY]
    # For development and jenkins do not send email notification to getTalent admins.
    if env == 'dev' or env == 'jenkins':
        return

    server_type = "Stage" if env == 'qa' else "Production"
    body = "%s\n\n\n\nRequest:\n%s" % (body, request)
    source = get_default_email_info()['source']
    send_email(source=source, subject="Talent Web %s %s: %s" % (server_type, prefix, subject), body=body,
               to_addresses=ADMINS)
