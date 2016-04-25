"""
Python logic for dealing with sent emails stored in s3. All exceptions and print statements
get sent to AWS CloudWatch when the lambda functions are deployed.

Emails are sent to resumes+<talent_pool_hash>@imports.gettalent.com
Amazon SES uploads that email as a text file to S3.
That s3 bucket triggers a lambda function on file upload.
lamda_handler() is called from AWS lambda and attempts to create a candidate from the resume.
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

from .models import session, Client, TalentPool, Token, User

RESUMES_BUCKET = 'resume-emails'
EMAIL_HASH_PATTERN = re.compile(r'\+(.+?)@')
AUTH_URL = 'http://localhost:8001/v1/oauth2/token'
RESUMES_URL = 'http://localhost:8003/v1/parse_resume'
PAYLOAD_QTY = 2

S3_CLIENT = boto3.client(
    's3',
    # aws_access_key_id='AKIAJBUXGOYRGOGOMULA',
    # aws_secret_access_key='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'
)


def lambda_handler(event, unused_context):
    """
    Extracts a resume attachment from an email uploaded to S3 and sends it to resumeParsing.
    :param dict event: The Lambda event dictionary.
    :param unused_context: A default  aws-lambda arg that is not used in this instance.
    :return None:
    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).decode('utf8')
    try:
        email_obj = S3_CLIENT.get_object(Bucket=RESUMES_BUCKET, Key=key)
        email_file = email.message_from_string(email_obj['Body'].read())
    except Exception as exception:
        print 'Error getting object {} from bucket {}. {}.'.format(key, bucket, exception)
        raise Exception

    validated_sender, talent_pool_hash = validate_email_file(email_file, key)
    access_token = get_user_access_token(validated_sender)
    raw_attachment = get_email_attachment(email_file, key)
    talent_pool_id = get_desired_talent_pool(talent_pool_hash)
    send_resume_to_service(access_token, raw_attachment, talent_pool_id, key)
    print 'Finished lambda event.'


def validate_email_file(email_file, key):
    """
    Consumes a email file, validates proper to/from, and extracts a supplied hash using '+'.
    :param email.message.Message email_file: Python std type email message.
    :param str key: The S3 key/"filename".
    :return tuple (str sender, str talent_pool_hash):
    """
    sender = email_file.get('From')
    if not sender:
        raise KeyError('Could not retrieve email sender with file {}'.format(key))
    receiver = email_file.get('To')
    if not receiver:
        raise KeyError('Could not retrieve email receiver with file {}'.format(key))
    talent_pool_hashes = EMAIL_HASH_PATTERN.findall(receiver)
    if not talent_pool_hashes:
        raise UserWarning('The email address {} did not specify a talentPool hash'.format(receiver))
    elif len(talent_pool_hashes) > 1:
        raise UserWarning('RegEx obtained more than one hash value from {}'.format(receiver))
    talent_pool_hash = talent_pool_hashes[0]
    return sender, talent_pool_hash


def get_user_access_token(email_address):
    """
    Retrieves a user's access token from the database and refreshes it if needed.
    :param str email_address: The email address being used to retrieve an access token.
    :return str: This is the Token.access_token we need to authenticate our getTalent API calls.
    """
    user = session.query(User).filter(User.email == email_address).first()
    if not user:
        raise UserWarning('Unable to retrieve a user with the email {}'.format(email_address))
    token = session.query(Token).filter(Token.user_id == user.Id).first()
    if not token:
        raise SQLAlchemyError('Unable to retrieve a token with the user_id {}'.format(user.Id))
    access_token = token.access_token
    if token.expires.replace(tzinfo=pytz.UTC) < utcnow():
        access_token = refresh_token(token)
    return access_token


def get_email_attachment(email_file, key):
    """
    For an email with an attachment the first item in payloads should be an email.message.Message
    with content-type of `multipart/alternative`. This then should produce another list of two items
    if you run .get_payloads() on that (one for plain text and another for HTML). In the event that
    there is no file attachment this 'nested email.message.Message' will be at the root. We test for
    this by validating the presence of a filename. The second item in the first list SHOULD be the
    file attachment. If multiple files are attached the payload count will increase for each file
    and raise a UserWarning.
    """
    payloads = email_file.get_payload()
    payload_count = len(payloads)
    if payload_count != PAYLOAD_QTY:
        raise UserWarning("User supplied incorrect payload count of {} from file {}".format(
            payload_count, key
        ))
    raw_attachment = payloads[1]
    if not raw_attachment.get_filename():
        raise UserWarning("User supplied no file from s3 file {}".format(key))
    return raw_attachment


def get_desired_talent_pool(simple_hash):
    """
    Queries the database for a talent_pool.id based on the simple_hash attr for it.
    :param str simple_hash: A < 10 char string that uniquely identifies a talent pool without
                            exposing the id.
    :return int:
    """
    session.commit() # Hacky fix for multiple sessions when testing =/
    talent_pool = session.query(TalentPool).filter(TalentPool.simple_hash == simple_hash).first()
    if not talent_pool:
        raise SQLAlchemyError('Unable to get talent_pool from hash {}'.format(simple_hash))
    return talent_pool.id


def utcnow():
    """
    Basic tz aware datetime objects: https://julien.danjou.info/blog/2015/python-and-timezones
    :return datetime.datetime:
    """
    return datetime.datetime.now(tz=pytz.utc)


def refresh_token(token_obj):
    """
    Refreshes an expired token.
    :param Token token_obj: A getTalent auth token.
    :return str: An updated access token after refreshing an expired access token.
    """
    grant_type = 'refresh_token'
    client_id = token_obj.client_id
    session.commit() # Hacky fix for multiple sessions when testing =/
    token_client = session.query(Client).filter(Client.client_id == client_id).first()
    if not token_client:
        raise SQLAlchemyError('Unable to get a client for User\'s token.id: {}'.format(
            token_obj.id))
    client_secret = token_client.client_secret

    payload = {
        'grant_type': grant_type,
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': token_obj.refresh_token
    }
    try:
        refresh_response = requests.post(AUTH_URL, data=payload)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exception:
        raise Exception('Error during token refresh! {}'.format(exception.message))
    token_json = json.loads(refresh_response.content)
    return token_json['access_token']


def send_resume_to_service(access_token, raw_attachment, talent_pool_id, key):
    """
    Formats and sends request to resumeParsingService
    :param str access_token: The access token used to authenticate API calls.
    :param str raw_attachment: This is a b64 encoded file (resume).
    :param int talent_pool_id: The talent pool that we wish to add this to (an arg in resume service)
    :param str key: The S3 key which is used for documenting exceptions raised in this process.
    :return None:
    """
    attachment_filename = raw_attachment.get_filename()
    headers = {
        'Authorization': 'Bearer {}'.format(access_token)
    }
    with open('/tmp/' + attachment_filename, 'w') as outfile:
        outfile.write(raw_attachment.get_payload().decode('base64'))
    payload = {
        'resume_file_name': attachment_filename,
        'create_candidate': True,
        'talent_pool_ids': [talent_pool_id]
    }
    with open('/tmp/' + attachment_filename, 'r') as infile:
        try:
            resume_response_response = requests.post(RESUMES_URL, headers=headers, data=payload,
                                                     files=dict(resume_file=infile))
            response_content = json.loads(resume_response_response.content)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            raise Exception('Error during POST to resumeParsingService')
    if resume_response_response.status_code is not requests.codes.ok:
        raise AssertionError('Candidate was not created from email {}. Content {}'.format(
            key, response_content))
    else:
        print 'Candidate created from {}, with id {}'.format(
            key, response_content['candidate']['id'])
