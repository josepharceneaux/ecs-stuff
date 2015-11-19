import re
import boto

AWS_ACCESS_KEY_ID = 'AKIAI3422SZ6SL46EYBQ'
AWS_SECRET_ACCESS_KEY = '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'
DEFAULT_MAIL_SENDER = '"getTalent Web" <no-reply@gettalent.com>'


def get_boto_ses_connection():
    conn = boto.connect_ses(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    return conn


def safe_send_email(source, subject, body, to_addresses, html_body=None, text_body=None, reply_address=None,
                    email_format='text'):
    """
    Returns None message_id if failed
    # TODO: Check this function
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
        from admin_reporting import email_error_to_admins

        email_error_to_admins(
            'email=%s, subject=%s, body=%s, html_body=%s, text_body=%s, error=%s' % (
                to_addresses, subject, body, html_body, text_body, e),
            'Email failed to send'
        )
    return dict(request_id=request_id, message_id=message_id)


def send_email(source, subject, body, to_addresses, html_body=None, text_body=None, reply_address=None, email_format='text'):
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

__author__ = 'jitesh'
