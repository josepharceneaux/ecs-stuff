"""
Library for integrating with Workday accounts. Provides a class implementing the standard ATS interface methods.
"""


import requests
import json

from urlparse import urlparse
from sqlalchemy import text


# Import path is different if we're loaded from script (as opposed to uswgi app)
if __name__ == 'ats.workday':
    from common.models.workday import WorkdayTable
else:
    from ats_service.common.models.workday import WorkdayTable


class Workday(object):
    """
    Class representing data we need to use the Workday API.
    """

    def __init__(self, logger, ats_name, login_url, user_id, credentials):
        """
        Initialize our object.
        """
        self.logger = logger
        self.ats_name = ats_name
        self.login_url = login_url
        url_object = urlparse(login_url)
        # Server location without URL components
        self.service = url_object.scheme + '://' + url_object.netloc
        self.user_id = user_id
        self.auth_token = None
        self.credentials = credentials
        self.fetch_candidates_url = "{}/all-individuals".format(self.service)
        self.fetch_individual_url = "{}/individual".format(self.service)

    def authenticate(self):
        """
        Perform authencation using our credentials, and store any tokens on this object.
        """
        self.logger.info("GET {}".format(self.login_url))
        response = requests.request('GET', self.login_url)
        # TODO: self.auth_token = json.loads(response.text)['token']
        self.auth_token = 'auth_token'
        self.logger.info("GET {}".format(response.text))

    def fetch_individual_references(self):
        """
        Fetch a list of references to individuals (could be candidates, employees, others)
        """
        self.logger.info("GET {}".format(self.fetch_candidates_url))
        response = requests.request('GET', self.fetch_candidates_url)
        return json.loads(response.text)

    def fetch_individual(self, reference):
        """
        Fetch the data for one individual. To be combined with previous method.

        :param string reference: The Workday reference (i.e., identifier) for this individual.
        """
        self.logger.info("GET {}".format(self.fetch_individual_url))
        response = requests.request('GET', self.fetch_individual_url + "/{}".format(reference))
        return response.text

    def save_individual(self, data, candidate_id):
        """
        Save an individual to the Workday table.

        :param string data: JASON description of individual.
        :param int candidate_id: id into the ATS Candidate table.
        """
        data_dict = json.loads(data)
        reference = data_dict['ats_remote_id']
        profile = json.loads(data_dict['profile_json'])['data']
        self.logger.info("SAVE {} {}".format(reference, profile))

        individual = WorkdayTable.get_by_reference(reference)
        if individual:
            individual.pre_hire_reference = str(profile['pre_hire_reference'])
            individual.worker_reference = str(profile['worker_reference'])
            individual.name_data = str(profile['name_data'])
            individual.contact_data = str(profile['contact_data'])
            individual.social_media_data = str(profile['social_media_account_data'])
            individual.status_data = str(profile['status_data'])
            individual.job_application_data = str(profile['job_application_data'])
            individual.prospect_data = str(profile['prospect_data'])
            individual.candidate_id_data = str(profile['candidate_id_data'])
        else:
            individual = WorkdayTable(ats_candidate_id=candidate_id,
                                      workday_reference=reference,
                                      pre_hire_reference=str(profile['pre_hire_reference']),
                                      worker_reference=str(profile['worker_reference']),
                                      name_data=str(profile['name_data']),
                                      contact_data=str(profile['contact_data']),
                                      social_media_data=str(profile['social_media_account_data']),
                                      status_data=str(profile['status_data']),
                                      job_application_data=str(profile['job_application_data']),
                                      prospect_data=str(profile['prospect_data']),
                                      candidate_id_data=str(profile['candidate_id_data']))

        individual.save()
        return individual

    @staticmethod
    def workday_email_from_contact_data(data):
        """
        Workday Candidate Contact Data contains phone number, email address, website data and location data.
        Exact format TBD.
        :param string data: String containing elements above.
        """
        # Fake it for now
        return [ 'joe@gettalent.com' ]

    @staticmethod
    def workday_phone_from_contact_data(data):
        """
        Workday Candidate Contact Data contains phone number, email address, website data and location data.
        Exact format TBD.
        :param string data: String containing elements above.
        """
        # Fake it for now
        return [ '415 203 8545' ]

    @staticmethod
    def get_individual_contact_email_address(ats_candidate):
        """
        Return (from our local database) the main contact email address for an individual

        :param ATSCandidate ats_candidate: ATSCandidate object.
        """
        # Get WorkdayTable entry
        individual = WorkdayTable.get_by_ats_id(ats_candidate.id)
        if not individual:
            return []

        # Extract email address from contact_data
        email_list = workday_email_from_contact_data(individual.contact_data)

        return email_list

    @staticmethod
    def get_individual_contact_phone_number(ats_candidate):
        """
        Return (from our local database) the main contact phone number for an individual

        :param ATSCandidate ats_candidate: ATSCandidate object.
        """
        # Get WorkdayTable entry
        individual = WorkdayTable.get_by_ats_id(ats_candidate.id)
        if not individual:
            return []

        # Extract email address from contact_data
        phone_numbers = workday_phone_from_contact_data(individual.contact_data)

        return phone_numbers
