__author__ = 'ufarooqi'

import boto
import os
import re
from flask import current_app as app
from ..talent_config_manager import TalentConfigKeys


def get_boto_ses_connection():
    conn = boto.connect_ses(aws_access_key_id=app.config[TalentConfigKeys.AWS_KEY],
                            aws_secret_access_key=app.config[TalentConfigKeys.AWS_SECRET])
    return conn


def get_default_email_info():
    """
    This functions returns default email information which will be used while sending email (hopefully in
    case of email campaigns).
    It is different for different environments and it is taken from web.cfg either from file
    system or from Amazon S3 bucket.
    Possible values for default emails are:
        Development : no-reply-local@gettalent.com
        Jenkins     : no-reply-jenkins@gettalent.com
        Production  : no-reply@gettalent.com
    :rtype dict
    """
    return {'email': app.config[TalentConfigKeys.DEFAULT_MAIL_SENDER],
            'source': '"getTalent Web" <%s>' % app.config[TalentConfigKeys.DEFAULT_MAIL_SENDER]}


def safe_send_email(source, subject, body, to_addresses, html_body=None, text_body=None, reply_address=None,
                    email_format='text'):
    """
    Returns None message_id if failed
    """

    message_id = None
    try:
        email_response = send_email(source, subject, body, to_addresses, html_body=html_body, text_body=text_body,
                                    reply_address=reply_address, email_format=email_format)
        request_id = email_response[u"SendEmailResponse"][u"ResponseMetadata"][u"RequestId"]
        message_id = email_response[u"SendEmailResponse"][u"SendEmailResult"][u"MessageId"]
    except Exception, e:
        # If failed to send email, still try to get request id from XML response.
        # Unfortunately XML response is malformed so must manually parse out request id
        request_id_search = re.search('<RequestId>(.*)</RequestId>', e.__str__(), re.IGNORECASE)
        request_id = request_id_search.group(1) if request_id_search else None

        # Send failure message to email marketing admin, just to notify for verification
        from talent_reporting import email_error_to_admins

        email_error_to_admins(
            'email=%s, subject=%s, body=%s, html_body=%s, text_body=%s, error=%s' % (
                to_addresses, subject, body, html_body, text_body, e),
            'Email failed to send'
        )

    return dict(request_id=request_id, message_id=message_id)


def send_email(source, subject, body, to_addresses, html_body=None, text_body=None,
               reply_address=None, email_format='text'):
    conn = get_boto_ses_connection()
    email_result = conn.send_email(
        source=source,
        subject=subject,
        body=body,
        html_body=html_body,
        text_body=text_body,
        to_addresses=to_addresses,
        reply_addresses=reply_address,
        format=email_format
    )
    return email_result
