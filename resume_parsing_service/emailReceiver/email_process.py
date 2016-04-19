"""Python logic for dealing with sent emails stored in s3. All exceptions and print statements
   get sent to AWS CloudWatch when the lambda functions are deployed.
"""
import urllib
import datetime
import email
import re
import json

import boto3
import pytz
import requests
from sqlalchemy.exc import SQLAlchemyError

from models import session, Client, Token, User

RESUMES_BUCKET = 'resume-emails'
EMAIL_HASH_PATTERN = re.compile(r'\+(.+?)\@')
AUTH_URL = 'http://localhost:8001/v1/oauth2/token'
RESUMES_URL = 'http://localhost:8003/v1/parse_resume'

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
    # TODO get talent pool id
    user = session.query(User).filter(User.email==sender).first()
    if not user:
        raise UserWarning('Unable to retrieve a user with the email {}'.format(sender))
    token = session.query(Token).filter(Token.user_id==user.Id)
    if not token:
        raise SQLAlchemyError('Unable to retrieve a token with the user_id {}'.format(user.Id))
    access_token = token.access_token
    if token.expires < utcnow():
        access_token = refreshToken(token)
    """
    For an email with an attachment the first item in payloads should be an email.message.Message
    with content-type of `multipart/alternative`. This then should produce another list of two items
    if you run .get_payloads() on that (one for plain text and another for HTML). The second item in
    the first list should be the file attachment.
    """
    payloads = email_file.get_payload()
    if len(payloads) < 2:
        raise UserWarning('User email {} does not have sufficient payload.'.format(key))
    raw_attachment = payloads[1]
    attachment_filename = raw_attachment.get_filename()
    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
        'Content-Type': 'application/json'
    }
    with open('/tmp/' + attachment_filename, 'w') as outfile:
        outfile.write(raw_attachment)
        payload = {
            'resume_file_name': attachment_filename,
            'resume_file': outfile,
            'create_candidate': True,
            # 'talent_pool_id': foo
        }
        try:
            resume_response_response = requests.post(RESUMES_URL, headers=headers, data=payload)
            response_content = json.loads(resume_response_response.content)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            raise e('Error during POST to resumeParsingService')
    if resume_response_response.status_code is not requests.codes.ok:
        raise AssertionError('Candidate was not created from email {}. Content {}'.format(
            key, response_content))
    else:
        print 'Candidate created from {}, with id {}'.format(key, response_content['candidate']['id'])


def utcnow():
    """
    Basic tz aware datetime objects: https://julien.danjou.info/blog/2015/python-and-timezones
    :return datetime.datetime:
    """
    return datetime.datetime.now(tz=pytz.utc)


def refreshToken(tokenObj):
    """
    Refreshes an expired token.
    :param Token tokenObj:
    :return Token:
    """
    GRANT_TYPE = 'refresh_token'
    client_id = tokenObj.client_id
    token_client = session.query(Client).filter(Client.client_id==client_id)
    if not token_client:
        raise SQLAlchemyError('Unable to get a client for User\'s token.id: {}'.format(tokenObj.id))
    CLIENT_SECRET = token_client.client_secret
    refresh_token = 'refresh_bar'

    payload = {
      'grant_type': GRANT_TYPE,
      'client_id': client_id,
      'client_secret': token_client.client_secret,
      'refresh_token': tokenObj.refresh_token
    }
    try:
        refresh_response = requests.post(AUTH_URL, data=payload)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        raise e('Error during token refresh!')
    token_json = json.loads(refresh_response.content)
    return token_json.access_token
