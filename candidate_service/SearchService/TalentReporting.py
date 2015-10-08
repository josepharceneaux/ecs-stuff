# -*- coding: utf-8 -*-
from gluon import current

ADMINS = ['osman@gettalent.com', 'vincent.mendolia@dice.com', 'ahmed@janim.me', 'jitesh.karesia@newvisionsoftware.in', 'ashwin@gettalent.com', 'umar.farooqi.gt@gmail.com']


def email_error_to_admins(body, subject=""):
    current.logger.error("Admin notification: \nSubject=%s\nBody=%s", subject, body)
    email_admins(body, "Error", subject)


def email_notification_to_admins(body, subject=""):
    current.logger.info("Admin notification: \nSubject=%s\nBody=%s", subject, body)
    email_admins(body, "Notification", subject)


def email_admins(body, prefix, subject):
    import TalentPropertyManager
    if TalentPropertyManager.get_env() == 'dev' or current.IS_TEST:
        return

    is_dev = current.IS_DEV
    mail = current.mail

    server_type = "Dev" if is_dev else "Production"
    body = "%s\n\n\n\nRequest env:\n%s\n\nRequest vars:\n%s" % (body, current.request.env, current.request.vars)
    mail.send(to=ADMINS,
              subject="Talent Web %s %s: %s" % (server_type, prefix, subject),
              message=body)
