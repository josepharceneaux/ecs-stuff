__author__ = 'amirhb'
from flask import jsonify
# from email_campaign import logger

# Todo: import response
def forbidden(message):
    response = jsonify({'error': {'code': 100, 'message': message}})
    response.status_code = 403
    return response


def email_error_to_admins(body, subject=""):
    logger.error("Admin notification: \nSubject=%s\nBody=%s", subject, body)
    email_admins(body, "Error", subject)
    return 'error'

def email_notification_to_admins(body, subject=""):
    logger.info("Admin notification: \nSubject=%s\nBody=%s", subject, body)
    email_admins(body, "Notification", subject)


def email_admins(body, prefix, subject):
    return ''
