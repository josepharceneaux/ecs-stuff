from abc import ABCMeta, abstractmethod
from SocialNetworkService.custom_exections import EventNotSaveInDb
from SocialNetworkService.utilities import get_message_to_log, log_error
from common.gt_models.event import Event


class EventBase(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        function_name = '__init__()'
        self.message_to_log = get_message_to_log(function_name=function_name,
                                                 class_name=self.__class__.__name__)

        self.events = []
        self.rsvps = []
        self.user_id = kwargs['user_id']
        self.api_url = kwargs['api_url']
        self.headers = kwargs['headers']

    @abstractmethod
    def create_event(self, *args, **kwargs):
        pass

    def delete_events(self, event_ids):
        deleted = []
        not_deleted = []
        if len(event_ids) > 0:
            for event_id in event_ids:
                event = Event.get_by_user_and_event_id(self.user_id, event_id)
                if event:
                    try:
                        self.unpublish_event(event.vendorEventId)
                        Event.delete(event_id)
                        deleted.append(event_id)
                    except Exception as e:     # some error while removing event
                        not_deleted.append(event_id)
                else:
                    not_deleted.append(event_id)
        return deleted, not_deleted

    def get_events(self, *args, **kwargs):
        pass

    def save_event(self, data):
        """
        This function serves the storage of event in database after it is
        successfully published.
        :param data:
        :return:
        """
        function_name = 'save_event()'
        self.message_to_log.update({'function_name': function_name})
        sn_event_id = data['vendorEventId']
        socail_network_id = data['socialNetworkId']
        event = Event.get_by_user_id_social_network_id_vendor_event_id(
            self.user_id,
            socail_network_id,
            sn_event_id)
        try:
            if event:
                event.update(**data)
                Event.session.commit()
            else:
                event = Event(**data)
                Event.save(event)
        except Exception as e:
            error_message = 'Event was not saved in Database\nError: %s' % str(e)
            self.message_to_log.update({'error': error_message})
            log_error(self.message_to_log)
            raise EventNotSaveInDb('Error occurred while saving event in databse')
        return event.id

    def event_sn_to_gt_mapping(self, *args, **kwargs):
        pass

    def event_gt_to_sn_mapping(self, *args, **kwargs):
        pass
