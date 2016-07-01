"""Utilities related to the parsing of resumes."""
# pylint: disable=wrong-import-position, fixme, import-error
__author__ = 'erikfarmer'
# Standard Library
import hashlib
import json
from cStringIO import StringIO
# Third Party
from flask import current_app
import boto3
import requests
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.common.error_handling import InvalidUsage, InternalServerError
from resume_parsing_service.common.routes import CandidateApiUrl, CandidatePoolApiUrl
from resume_parsing_service.common.utils.talent_s3 import boto3_get_file


def create_parsed_resume_candidate(candidate_dict, formatted_token_str, filename):
    """
    Sends candidate dict to candidate service POST and returns response.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param str formatted_token_str: string in format 'Bearer foo'.
    :return tuple (bool, int):
    """
    try:
        create_response = requests.post(CandidateApiUrl.CANDIDATES,
                                        timeout=20,
                                        data=json.dumps({'candidates': [candidate_dict]}),
                                        headers={'Authorization': formatted_token_str,
                                                 'Content-Type': 'application/json'})

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("create_parsed_resume_candidate. Could not reach CandidateService POST")
        raise InternalServerError("Unable to reach Candidates API during candidate creation")

    # Handle bad responses from Candidate Service.
    if create_response.status_code in xrange(500, 511):
        raise InternalServerError('Error in response from candidate service during creation')

    response_dict = json.loads(create_response.content)

    # Handle other non 201 responses.
    if create_response.status_code is not requests.codes.created:

        #If a candidate has been created already it will provide an id.
        existing_candidate_id = response_dict.get('error', {}).get('id')

        if existing_candidate_id:
            return False, existing_candidate_id

        # If there was an issue with candidate creation we want to forward the error message and
        # the error code supplied by Candidate Service.
        else:
            candidate_service_error = response_dict.get('error', {}).get('message')

            if candidate_service_error:
                error_text = candidate_service_error + ' Filename: {}'.format(filename)

            else:
                error_text = 'Error in candidate creating from resume service. Filename {}'.format(filename)

            raise InvalidUsage(error_message=error_text)



    # Candidate was created. Return bool and id
    else:
        candidate_id = response_dict.get('candidates')[0]['id']
        logger.debug('Candidate created with id: {}'.format(candidate_id))
        return True, candidate_id


def update_candidate_from_resume(candidate_dict, formatted_token_str, filename_str):
    """
    Sends candidate dict to candidate service PATCH and returns response. If the update is not
    successfull it will raise an error.
    :param dict candidate_dict: dict containing candidate info in candidate format.
    :param str formatted_token_str: string in format 'Bearer foo'.
    :return bool:
    """
    try:
        update_response = requests.patch(CandidateApiUrl.CANDIDATES,
                                         timeout=20,
                                         data=json.dumps({'candidates': [candidate_dict]}),
                                         headers={'Authorization': formatted_token_str,
                                                  'Content-Type': 'application/json'})
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.exception("update_candidate_from_resume. Could not reach CandidateService PATCH")
        raise InternalServerError("Unable to reach Candidates API in during candidate update")

    if update_response.status_code is not requests.codes.ok:
        logger.info(
            "ResumetoCandidateError. {} received from CandidateService (update)".format(
                update_response.status_code))

        raise InternalServerError(
            'Candidate from {} exists, error updating info'.format(filename_str))

    response_dict = json.loads(update_response.content)
    candidate_id = response_dict.get('candidates')[0]['id']
    logger.debug('Candidate updated with id: {}'.format(candidate_id))

    return True


def send_candidate_references(candidate_references, candidate_id, oauth_string):
    """
    Makes an attempt to create references for a candidate using their id. Failure does not raise an
    exception as this would prevent the candidate creation life cycle, but instead logs the issue.
    :param string candidate_references:
    :param string candidate_id:
    :param string oauth_string:
    :return None:
    """
    post_body = {
        'candidate_references': [
            {'comments': candidate_references}
        ]
    }

    try:
        references_response = requests.post(
            CandidateApiUrl.REFERENCES % candidate_id, data=json.dumps(post_body),
            headers={'Authorization': oauth_string,
                     'Content-Type': 'application/json'})

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.warn(
            "process_resume. Connection error creating candidate {} references.".format(candidate_id))

    if references_response.status_code is not requests.codes.created:
        logger.warn("process_resume. Error creating candidate {} references. {}".format(
            candidate_id, references_response.content))


def get_users_talent_pools(formatted_token_str):
    """
    Uses the candidate pool service to get talent pools of a user's domain via their token.
    :param str formatted_token_str: "bearer foo" formatted string; as it appears in header.
    :return: List of talent pools ids
    :rtype: list
    """
    try:
        talent_pool_response = requests.get(CandidatePoolApiUrl.TALENT_POOLS,
                                            headers={'Authorization': formatted_token_str})
    except requests.exceptions.ConnectionError:
        raise InvalidUsage("ResumeParsingService could not reach CandidatePool API in get_users_talent_pools")

    talent_pools_response = json.loads(talent_pool_response.content)

    if 'error' in talent_pools_response:
        raise InvalidUsage(error_message=talent_pools_response['error'].get(
            'message', 'Error in getting user talent pools.'))

    try:
        return [talent_pools_response['talent_pools'][0]['id']]

    except IndexError:
        return []


def gen_hash_from_file(_file):
    """Handy function for creating file hashes. Used as redis keys to store parsed resumes."""
    return hashlib.md5(_file.read()).hexdigest()


def send_abbyy_email():
    """
    Function to send warning emails in the event Abbyy is out of credits. If RPS uses ses
    functionality more this can be made more modular.
    :return dict:
    """

    email_client = boto3.client('ses', region_name='us-east-1')
    # Send to work/personal of DRI as well as Osman as back up in the event DRI is unavailable.
    recipients = ['erik@gettalent.com', 'erikdfarmer@gmail.com', 'osman@gettalent.com']
    ses_source = 'no-reply@gettalent.com'
    subject = 'RED ALERT - Abbyy OCR is out of credits!'
    body = 'Purchase credits from: https://cloud.ocrsdk.com/Account/Welcome immediately\n'

    response = email_client.send_email(
        Source=ses_source,
        Destination={'ToAddresses': recipients},
        Message={
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text': {
                    'Data': body
                }
            }
        }
    )
    return response


def resume_file_from_params(parse_params):
    """
    Obtains a resume from the POST JSON data.
    :param parse_params:
    :return:
    """
    filepicker_key = parse_params.get('filepicker_key')

    if filepicker_key:
        resume_bucket = current_app.config['S3_FILEPICKER_BUCKET_NAME']
        resume_file = boto3_get_file(resume_bucket, filepicker_key)
    elif parse_params.get('filename'):
        resume_bin = parse_params.get('resume_file')
        resume_file = StringIO(resume_bin.read())

    else:
        raise InvalidUsage('Invalid query params for /parse_resume')

    return resume_file
