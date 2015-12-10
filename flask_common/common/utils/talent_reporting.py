__author__ = 'ufarooqi'

import os
from flask import request
from flask_mail import Message
from flask import current_app as app
from amazon_ses import mail

ADMINS = ['osman@gettalent.com', 'vincent.mendolia@dice.com', 'ahmed@janim.me', 'jitesh.karesia@newvisionsoftware.in',
          'ashwin@gettalent.com', 'umar.farooqi.gt@gmail.com']


def email_error_to_admins(body, subject=""):
    email_admins(body, "Error", subject)


def email_notification_to_admins(body, subject=""):
    email_admins(body, "Notification", subject)


def email_admins(body, prefix, subject):

    env = os.environ.get('GT_ENVIRONMENT')
    if env == 'dev' or env == 'circle':
        return

    server_type = "Stage" if env == 'qa' else "Production"
    body = "%s\n\n\n\nRequest:\n%s" % (body, request)

    message = Message("Talent Web %s %s: %s" % (server_type, prefix, subject), recipients=ADMINS, body=body)
    mail.init_app(app)
    mail.send(message)