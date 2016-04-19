"""Python logic for dealing with sent emails stored in s3."""
import urllib
import datetime
import email
import re

import boto3
import pytz
from sqlalchemy.exc import SQLAlchemyError

from models import session, Token, User

RESUMES_BUCKET = 'resume-emails'
EMAIL_HASH_PATTERN = re.compile(r'\+(.+?)\@')

s3_client = boto3.client(
    's3',
    aws_access_key_id='AKIAJBUXGOYRGOGOMULA',
    aws_secret_access_key='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'
)

def lambda_handler(event, context):
    """
    Basic conversion of email file from s3 and upload extracted file attachment.
    :param event:
    :param context:
    :return:
    """

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).decode('utf8')
    try:
        email_obj = s3_client.get_object(Bucket=RESUMES_BUCKET, Key=key)
        email_file = email.message_from_string(email_obj['Body'].read())
    except Exception as e:
        print('Error getting object {} from bucket {}. {}.'.format(key, bucket, e))
        raise e
    sender = email_file.get('From')
    if not sender:
        raise KeyError('Could not retrieve email sender with file {}'.format(key))
    receiver = email_file.get('To')
    if not receiver:
        raise KeyError('Could not retrieve email receiver with file {}'.format(key))
    talent_pool_hashes = EMAIL_HASH_PATTERN.findall(sender)
    if not talent_pool_hashes:
        raise UserWarning('The email address {} did not specify a talentPool hash'.format(receiver))
    elif len(talent_pool_hashes) > 1:
        raise UserWarning('RegEx obtained more than one hash value from {}'.format(receiver))
    user = session.query(User).filter(User.email==sender).first()
    if not user:
        raise UserWarning('Unable to retrieve a user with the email {}'.format(sender))
    token = session.query(Token).filter(Token.user_id==user.Id)
    if not token:
        raise SQLAlchemyError('Unable to retrieve a token with the user_id {}'.format(user.Id))
    if token.expires < utcnow():
        token = refreshToken(token)
    # Refresh if needed
    # Form resume request with file.
    # attachment = email_file.get_payload()[1]
    # with open('/tmp/' + attachment.get_filename(), 'w') as outfile:
    #     outfile.write(attachment.get_payload())
    #     s3_client.upload_file('/tmp/' + attachment.get_filename(), 'resume-emails', attachment.get_filename())


def utcnow():
    """
    Basic tz aware datetime objects: https://julien.danjou.info/blog/2015/python-and-timezones
    :return datetime.datetime:
    """
    return datetime.datetime.now(tz=pytz.utc)


def refreshToken(tokenObj):
    """
    Refreshes an expired token.
    :param models.Token tokenObj:
    :return models.Token:
    """
    return tokenObj
