from abc import abstractmethod, ABCMeta
from event_exporter.common import _get_message_to_log, _log_error, http_request
from gt_models.social_network import SocialNetwork
from gt_models.user import User, UserCredentials


class TalentEventBase(object):
    """
    This is the base class which is extended by vendor child classes
    This provides necessary interface which will be implemented by all child
    classes.
    """
    __metaclass__ = ABCMeta

    def __init__(self, social_network_name, *args, **kwargs):
        """
        Initialize required class variables to be used later.
        :param args:
        :param kwargs:
        :return:
        """
        user_id = kwargs['user_id']

        self.user = User.get_by_id(user_id)
        social_network = SocialNetwork.get_by_name(social_network_name)
        social_network_id = social_network.id

        function_name = '__init__()'
        message_to_log = _get_message_to_log(function_name=function_name,
                                             class_name='TalentEventBase')
        user_credentials = UserCredentials.get_by_user_and_social_network(user_id, social_network_id)

        if user_credentials:
            self.user_credentials = user_credentials
            self.access_token = user_credentials.accessToken
        else:
            error_message = 'User Credentials are None'
            message_to_log.update({'error': error_message})
            _log_error(message_to_log)
        if social_network and social_network.apiUrl:
            self.api_url = social_network.apiUrl
        else:
            error_message = 'API Url missing from User Credentials'
            message_to_log.update({'error': error_message})
            _log_error(message_to_log)
        # Eventbrite and meetup social networks take access token in header
        # so here we generate authorization header to be used by both of them
        self.headers = {'Authorization': 'Bearer ' + self.access_token}
        self.message_to_log = _get_message_to_log()

    @abstractmethod
    def create_event(self):
        return

    @abstractmethod
    def get_mapped_data(self, data):
        return

    def post_data(self, url, payload):
        """
        This function is used to make a POST call to the provided url
        It uses http_request() method defined on top of file
        :param url: url to which post call is supposed to be made
        :param payload: payload is used as parameters in post call
        :return: response of POST call
        """
        result = http_request('POST', url, params=payload, headers=self.headers,
                              message_to_log=self.message_to_log)
        return result

    def get_data(self, url, payload):
        """
        This function is used to make a get call to the provided url
        It uses http_request() method defined on top of file
        :param url: url to which post call is supposed to be made
        :param payload: payload is used as parameters in post call
        :return: response of GET call
        """
        result = http_request('GET', url, params=payload, headers=self.headers,
                              message_to_log=self.message_to_log)
        return result