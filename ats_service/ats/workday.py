"""
Library for integrating with Workday accounts.
"""


import requests
import json

from urlparse import urlparse

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
        self.service = url_object.scheme + '://' + url_object.netloc
        self.user_id = user_id
        self.auth_token = None
        self.credentials = credentials
        self.fetch_candidates_url = "{}/all-individuals".format(self.service)
        self.fetch_individual_url = "{}/individual".format(self.service)

    def authenticate(self, credentials):
        """
        Perform authencation using our credentials, and store any tokens on this object.
        """
        self.logger.info("GET {}".format(self.login_url))
        auth_token = 'auth_token'
        response = requests.request('GET', self.login_url)
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
        """
        self.logger.info("GET {}".format(self.fetch_individual_url))
        response = requests.request('GET', self.fetch_individual_url + "/{}".format(reference))
        return response.text

    def save_individual(self, data, candidate_id):
        """
        Save an individual to the Workday table.

        :param string data: Jason description of individual.
        :param int candidate_id: id into the ATS Candidate table.
        """
        data_dict = json.loads(data)
        reference = data_dict['ats_remote_id']
        profile = json.loads(data_dict['profile_json'])['data']
        self.logger.info("SAVE {} {}".format(reference, profile))
        self.logger.info("SOCIAL {}".format(profile['social_media_account_data']))
