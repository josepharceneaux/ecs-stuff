"""Utilities related to the parsing of resumes."""
# pylint: disable=wrong-import-position, fixme
__author__ = 'erikfarmer'
# Standard Library
import hashlib
import json
# Third Party
import boto3
import requests
# Module Specific
from resume_parsing_service.app import logger
from resume_parsing_service.common.error_handling import InvalidUsage, InternalServerError
from resume_parsing_service.common.routes import CandidateApiUrl, CandidatePoolApiUrl


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
        raise InternalServerError("Unable to reach Candidates API in during candidate creation")

    # Handle bad responses from Candidate Service.
    if create_response.status_code in xrange(500, 511):
        raise InternalServerError('Error in response from candidate service during creation')

    response_dict = json.loads(create_response.content)

    # Handle other non 201 responses.
    if create_response.status_code is not requests.codes.created:
        # If there was an issue with candidate creation we want to forward the error message and
        # the error code supplied by Candidate Service.
        existing_candidate_id = response_dict.get('error', {}).get('id')

        if not existing_candidate_id:
            candidate_error_message = response_dict.get('error', {}).get('message')

            if candidate_error_message:
                error_text = candidate_error_message + ' Filename: {}'.format(filename)

            else:
                error_text = 'Error in candidate creating from resume service. Filename {}'.format(
                    filename)

            raise InvalidUsage(error_message=error_text)

        if existing_candidate_id:
            return False, existing_candidate_id

    # Candidate was created. Return bool and id
    else:
        candidate_id = response_dict.get('candidates')[0]['id']
        logger.debug('Candidate created with id: {}'.format(candidate_id))
        return True, candidate_id

        # We have a candidate already with this email so lets patch it up
        # parsed_resume['candidate']['id'] = existing_candidate_id
        # update_response = update_candidate_from_resume(parsed_resume['candidate'], oauth_string)
        #
        # if update_response.status_code is not requests.codes.ok:
        #     logger.info(
        #         "ResumetoCandidateError. {} received from CandidateService (update)".format(
        #             update_response.status_code))
        #
        #     raise InternalServerError(
        #         'Candidate from {} exists, error updating info'.format(filename_str))
        #
        # response_dict = json.loads(update_response.content)
        # logger.info('Response Dict: {}'.format(response_dict))
        #
        # candidate_id = response_dict.get('candidates')[0]['id']
        # logger.debug('Candidate created with id: {}'.format(candidate_id))
    # return create_response


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


# TODO: write tests for this.
def get_users_talent_pools(formatted_token_str):
    """
    Uses the candidate pool service to get talent pools of a user's domain via their token.
    :param str formatted_token_str: "bearer foo" formatted string; as it appears in header.
    :return: List of talent pools ids
    :rtype: list
    """
    try:
        talent_pool_request = requests.get(CandidatePoolApiUrl.TALENT_POOLS,
                                           headers={'Authorization': formatted_token_str})
    except requests.exceptions.ConnectionError:
        raise InvalidUsage("ResumeParsingService could not reach CandidatePool API in "
                           "get_users_talent_pools")
    talent_pools_response = json.loads(talent_pool_request.content)
    if 'error' in talent_pools_response:
        raise InvalidUsage(error_message=talent_pools_response['error'].get(
            'message', 'Error in getting user talent pools.'))
    try:
        return [talent_pools_response['talent_pools'][0]['id']]
    except IndexError:
        return []


def gen_hash_from_file(_file):
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
