"""
Author: Hafiz Muhammad Basit, QC-Technologies,
        Lahore, Punjab, Pakistan <basit.gettalent@gmail.com>

This module contains CampaignBase class which provides common methods for
all campaigns. Methods are
- schedule()
- get_candidates()
- create_or_update_url_conversion()
- create_activity()
- get_campaign_data()
- save()
- process_send() etc.
Any service can inherit from this class to implement functionality accordingly.
"""

# Standard Library
import json
from abc import ABCMeta
from datetime import datetime
from abc import abstractmethod

# Third Party
from celery import chord
from flask import current_app

# Application Specific
from ..models.user import Token
from ..models.misc import UrlConversion
from ..models.candidate import Candidate
from ..utils.app_rest_urls import CandidateApiUrl, ActivityApiUrl
from ..utils.common_functions import http_request, find_missing_items, JSON_CONTENT_TYPE_HEADER
from ..error_handling import ForbiddenError, InvalidUsage, ResourceNotFound


class CampaignBase(object):
    """
    - This is the base class for sending campaign to candidates and to keep track
        of their responses.

    This class contains following methods:

    * __init__():
        This method is called by creating the class object.
        - It takes "user_id" as keyword argument and sets it in self.user_id.

    * save(self, form_data): [abstract]
        This method is used to save the campaign in db table according to campaign type.
        i.e. sms_campaign or push_notification_campaign etc. and returns the ID of
        new record in db.

    * process_send(self, campaign_id): [abstract]
        This method is used send the campaign to candidates. Child classes will implement this.

    * get_candidates(smart_list_id): [static]
        This method gets the candidates associated with the given smart_list_id.
        It may search candidates in database/cloud. It is common for all the campaigns.

    * send_sms_campaign_to_candidates(self, candidates):
        This loops over candidates and call send_sms_campaign_to_candidate to be send
        campaign asynchronously.

    * send_sms_campaign_to_candidate(self, candidates): [abstract]
        This does the sending part and update "sms_campaign_blast" and "sms_campaign_send".

    * create_or_update_url_conversion(destination_url=None, source_url='', hit_count=0,
                                    url_conversion_id=None, hit_count_update=None): [static]
        Here we save/update record of url_conversion in db table "url_conversion".
        This is common for all child classes.

    * create_activity(self, type_=None, source_table=None, source_id=None, params=None):
        This makes HTTP POST call to "activity_service" to create activity in database.
    """
    __metaclass__ = ABCMeta

    def __init__(self, user_id, *args, **kwargs):
        self.user_id = user_id
        self.oauth_header = self.get_authorization_header(self.user_id)
        self.campaign = None
        self.body_text = None  # This is 'text' to be sent to candidates as part of campaign.
        # Child classes will get this from respective campaign table.
        # e.g. in case of SMS campaign, this is get from "sms_campaign" database table.
        self.smart_list_id = None

    @staticmethod
    def get_authorization_header(user_id):
        """
        This returns the authorization header containing access token token associated
        with current user. We use this access token to communicate with other services,
        like activity_service to create activity.

        :param user_id: id of user
        :return: Authorization header
        :rtype: dict
        """
        user_token_row = Token.get_by_user_id(user_id)
        user_access_token = user_token_row.access_token
        if user_access_token:
            return {'Authorization': 'Bearer %s' % user_access_token}
        else:
            raise ForbiddenError(error_message='User(id:%s) has no auth token.' % user_id)

    @abstractmethod
    def save(self, form_data):
        """
        This saves the campaign in database table e.g. in sms_campaign or email_campaign etc.
        Child class will implement this.
        :return:
        """
        pass

    @abstractmethod
    def campaign_create_activity(self, source):
        """
        Child classes will use this to set type, source_id, source_table, params
        to create an activity in  database table "Activity" for newly created campaign.
        :return:
        """
        pass

    # TODO: implement after scheduler service is ready
    def schedule(self):
        """
        This actually POST on scheduler_service to schedule a given task.
        This will be common for all campaigns.
        :return:
        """
        pass

    @abstractmethod
    def process_send(self, campaign_id):
        """
        This will be used to do the processing to send campaign to candidates
        according to specific campaign. Child class will implement this.
        :return:
        """
        pass

    def get_candidates_from_candidate_service(self, smart_list_id):
        """
        This will get the candidates associated to a provided smart list. This makes
        HTTP GET call on candidate service API to get the candidate associated candidates.

        - This method is called from process_send() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :Example:
                SmsCampaignBase.get_candidates(smart_list_id=1)

        :param smart_list_id: id of smart list.
        :type smart_list_id: int
        :return: Returns array of candidates in the campaign's smart_lists.
        :rtype: list

        **See Also**
        .. see also:: process_send() method in SmsCampaignBase class.
        """
        params = {'id': smart_list_id,
                  'return': 'all'}
        # HTTP GET call to activity service to create activity
        url = CandidateApiUrl.SMARTLIST_CANDIDATES
        response = http_request('GET', url, headers=self.oauth_header, params=params,
                                user_id=self.user_id)
        # get candidate ids
        try:
            candidate_ids = [candidate['id'] for candidate in
                             json.loads(response.text)['candidates']]
            candidates = [Candidate.get_by_id(_id) for _id in candidate_ids]
            return candidates
        except Exception:
            current_app.logger.exception('get_candidates_from_candidate_service: Error while '
                                         'fetching candidates for smartlist(id:%s)' % smart_list_id)
            raise

    def send_campaign_to_candidates(self, candidates_and_phones):
        """
        Once we have the candidates, we iterate them and call
            self.send_campaign_to_candidate() to send the campaign to all candidates
            asynchronously.

        - This method is called from process_send() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param candidates_and_phones: Candidates associated to a smart list and their phones
        :type candidates_and_phones: list of tuples

        **See Also**
        .. see also:: process_send() method in SmsCampaignBase class.
        """
        # callback function which will be hit after campaign is sent to all candidates
        callback = self.callback_campaign_sent.subtask((self.user_id, self.campaign,
                                                        self.oauth_header, ))
        header = [self.send_campaign_to_candidate.subtask((self, record),
                                                          link_error=self.celery_error.subtask())
                  for record in candidates_and_phones]
        # This calls the callback function once all tasks in header have done their execution
        chord(header)(callback)

    @abstractmethod
    def send_campaign_to_candidate(self, candidate_and_phone):
        """
        This sends the campaign to given candidate. Child classes will implement this.
        :param candidate_and_phone: Candidate row and his phone
        :type candidate_and_phone: tuple
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def celery_error(error):
        """
        This function logs any error occurred for tasks running on celery,
        :return:
        """
        pass



    @staticmethod
    @abstractmethod
    def callback_campaign_sent(sends_result, user_id, campaign, auth_header):
        """
        This is the callback function for campaign sent.
        Child classes will implement this.
        :param sends_result: Result of executed task
        :param user_id: id of user (owner of campaign)
        :param campaign: id of campaign which was sent to candidates
        :param auth_header: auth header of current user to make HTTP request to other services
        :type sends_result: list
        :type user_id: int
        :type campaign: row
        :type auth_header: dict
        :return:
        """
        pass

    @staticmethod
    def create_or_update_url_conversion(destination_url=None, source_url=None, hit_count=0,
                                        url_conversion_id=None, hit_count_update=None):
        """
        - Here we save the source_url(provided in body text) and the shortened_url
            to redirect to our endpoint in db table "url_conversion".

        - This method is called from process_urls_in_sms_body_text() method of class
            SmsCampaignBase inside sms_campaign_service/sms_campaign_base.py.

        :param destination_url: link present in body text
        :param source_url: shortened URL of the link present in body text
        :param hit_count: Count of hits
        :param url_conversion_id: id of URL conversion record if needs to update
        :param hit_count_update: True if needs to increase "hit_count" by 1, False otherwise
        :type destination_url: str
        :type source_url: str
        :type hit_count: int
        :type url_conversion_id: int
        :type hit_count_update: bool
        :return: id of the url_conversion record in database
        :rtype: int

        **See Also**
        .. see also:: process_urls_in_sms_body_text() method in SmsCampaignBase class.
        """
        data = {'destination_url': destination_url,
                'source_url': source_url,
                'hit_count': hit_count}
        if url_conversion_id:  # record is already present in database
            record_in_db = UrlConversion.get_by_id(url_conversion_id)
            if record_in_db:
                data['destination_url'] = record_in_db.destination_url
                data['source_url'] = source_url if source_url else record_in_db.source_url
                data['hit_count'] = record_in_db.hit_count + 1 if hit_count_update else \
                    record_in_db.hit_count
                data.update({'last_hit_time': datetime.now()}) if hit_count_update else ''
                record_in_db.update(**data)
                url_conversion_id = record_in_db.id
            else:
                raise ResourceNotFound(
                    error_message='create_or_update_url_conversion: '
                                  'url_conversion(id:%s) not found' % url_conversion_id)
        else:
            missing_required_fields = find_missing_items(data, verify_all_keys=True)
            if len(missing_required_fields) == len(data.keys()):
                raise ForbiddenError(error_message='destination_url/source_url cannot be None.')
            else:
                new_record = UrlConversion(**data)
                UrlConversion.save(new_record)
                url_conversion_id = new_record.id
        return url_conversion_id

    @staticmethod
    def create_activity(user_id, type_=None, source_table=None, source_id=None,
                        params=None, headers=None):
        """
        - Once we have all the parameters to save the activity in database table "Activity",
            we call "activity_service"'s endpoint /activities/ with HTTP POST call
            to save the activity in db.

        - This method is called from create_sms_send_activity() and
            create_campaign_send_activity() methods of class SmsCampaignBase inside
            sms_campaign_service/sms_campaign_base.py.

        :param user_id: id of user
        :param type_: type of activity (using underscore with type as "type" reflects built in name)
        :param source_table: source table name of activity
        :param source_id: source id of activity
        :param params: params to store for activity
        :type user_id; int
        :type type_; int
        :type source_table: str
        :type source_id: int
        :type params: dict

        **See Also**
            .. see also:: create_sms_send_activity() method in SmsCampaignBase class.
        """
        if isinstance(params, dict):
            try:
                json_data = json.dumps({'source_table': source_table,
                                        'source_id': source_id,
                                        'type': type_,
                                        'params': params})
            except Exception as error:
                raise ForbiddenError(error_message='Error while serializing activity params '
                                                   'into JSON. Error is: %s' % error.message)
        else:
            raise InvalidUsage(error_message='params should be dictionary.')

        headers.update(JSON_CONTENT_TYPE_HEADER)
        # POST call to activity service to create activity
        url = ActivityApiUrl.CREATE_ACTIVITY
        http_request('POST', url, headers=headers, data=json_data, user_id=user_id)
