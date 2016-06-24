"""
This module contains constants related to Amazon Simple Notification Service (SNS) terminologies.
The values are fixed and specified by Amazon SNS service.
e.g. an email bounce message looks like
Headers:
    Content-Length: 1526
    X-Amz-Sns-Message-Type: SubscriptionConfirmation
    User-Agent: Amazon Simple Notification Service Agent
    X-Amz-Sns-Message-Id: af7c6567-456d-46cb-98e9-f311ae426664
    Host: emails.ngrok.io
    X-Forwarded-For: 72.21.217.155
    Content-Type: text/plain; charset=UTF-8
    Accept-Encoding: gzip,deflate
    X-Amz-Sns-Topic-Arn: arn:aws:sns:us-east-1:528222547498:email_bounces

Request Data:
    {u'SignatureVersion': u'1', u'Timestamp': u'2016-04-15T11:06:27.098Z',
    u'Signature': u'TlJPvXJhFUJwmj0QT6Ww/m9bO+5OWPtMOV8twx9uxnjm/JRoWYTH+xcpgqimOEinqExOj/WwwUG34A6Hysn0hbp1t3fNblohq0cJ9wNbu5snWEAUM8pW71SAPJF4m4HrWP6n5qRz7SUzGseqMrtw0vTf1f1HPdokF6/fLTPEZwXi2UwnewTGZmFCN7F8nmjCDDsZOFOk0V0FUS5pxYt1tIwCKw7tXJg69aiJvz1d3hLwGYLg7WrRaFqwlIRxNa/Sglru/kA/5Qz0hrhFFNhqpS1mOrZxUI9lFCU1p20eaQLHyrLVTKfz/8O3ihUQq2JBViEo7jhmnW4YBgWWfiBxiQ==',
    u'SigningCertURL': u'https://sns.us-east-1.amazonaws.com/SimpleNotificationService-bb750dd426d95ee9390147a5624348ee.pem', u'MessageId': u'9035f0c9-7d9e-54cc-a9d1-bf43b0ed685a',
    u'Message': u'{
        "notificationType":"Bounce",
        "bounce":{
            "bounceSubType":"General","bounceType":"Permanent",
            "reportingMTA":"dsn; a10-16.smtp-out.amazonses.com",
            "bouncedRecipients":[{
                "emailAddress":"invalid_21dc0a17-5d6c-4c90-94d5-43995440adca@gmail.com",
                "status":"5.1.1", "diagnosticCode":"smtp; 550-5.1.1 The email account that you tried to reach does not exist. Please try\\n550-5.1.1 double-checking the recipient\'s email address for typos or\\n550-5.1.1 unnecessary spaces. Learn more at\\n550 5.1.1  https://support.google.com/mail/answer/6596 i90si6763880qkh.85 - gsmtp",
                "action":"failed"}],
            "timestamp":"2016-04-15T11:06:27.050Z",
            "feedbackId":"010001541999befd-87ec56fd-dea4-42bd-aca3-c15f80fee63e-000000"
        },
        "mail":{
            "timestamp":"2016-04-15T11:06:26.000Z",
            "sendingAccountId":"528222547498",
            "source":"\\"cleannon@example.net\\" <no-reply@gettalent.com>",
            "messageId":"010001541999bc9d-30565a30-56ea-475f-b517-e477633ceb44-000000",
            "destination":["invalid_21dc0a17-5d6c-4c90-94d5-43995440adca@gmail.com"],
            "sourceArn":"arn:aws:ses:us-east-1:528222547498:identity/no-reply@gettalent.com"
        }
    }',
    u'UnsubscribeURL': u'https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:528222547498:email_bounces:9f7ad4f7-d58d-40e6-94fc-7ec6536e2176',
    u'Type': u'Notification', u'TopicArn': u'arn:aws:sns:us-east-1:528222547498:email_bounces'
}
"""
HEADER_KEY = 'X_AMZ_SNS_MESSAGE_TYPE'

# All these values represent some data in Amazon SNS Notification (http) request body
# -----------------------------------------------------------------------------------

# Request type can be subscription, unsubscription or Notification
SUBSCRIBE = 'SubscriptionConfirmation'
UNSUBSCRIBE = 'UnsubscribeConfirmation'
NOTIFICATION = 'Notification'

MESSAGE = 'Message'
MESSAGE_ID = 'messageId'
# Actual email information like messageId, source, destination etc.
MAIL = 'mail'

# Bounce object containing bounce information
BOUNCE = 'bounce'

NOTIFICATION_TYPE = 'notificationType'

# Notification type which can be Bounce, Complaint or Delivery (handling bounces and complaints only)
BOUNCE_NOTIFICATION = 'Bounce'
COMPLAINT_NOTIFICATION = 'Complaint'

# Bounce type, permanent or temporary
PERMANENT_BOUNCE = 'Permanent'
TEMPORARY_BOUNCE = 'Transient'

# Unique Amazon Resource Name
TOPIC_ARN = 'TopicArn'

# A url to confirm subscription for a SNS topic
SUBSCRIBE_URL = 'SubscribeURL'

# list of email recipients
BOUNCE_RECIPIENTS = 'bouncedRecipients'
EMAIL_ADDRESSES = 'emailAddress'
