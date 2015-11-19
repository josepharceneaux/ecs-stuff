# -*- coding: utf-8 -*-
from AWS_SES import send_email, DEFAULT_MAIL_SENDER

__author__ = 'jitesh'


ADMINS = ['osman@gettalent.com', 'vincent.mendolia@dice.com', 'ahmed@janim.me', 'jitesh.karesia@newvisionsoftware.in', 'ashwin@gettalent.com', 'umar.farooqi.gt@gmail.com']


def email_admins(env, subject, body, message_type='Notification'):
    if env in ['dev', 'circle']:
        # For development and circle ci do not send email notification to GetTalent admins.
        return
    # TODO: Create proper mail body so that it becomes easier to track the error.
    body = "%s\n\n\n\nRequest env:\n%s" % (body, env)
    send_email(source=DEFAULT_MAIL_SENDER, subject="%s: %s"%(message_type,subject), body=body, to_addresses=ADMINS)
