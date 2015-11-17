"""
This module contains SmsCampaignBase class inherited from CampaignBase.
This implements abstract methods of CampaignBase class and defines its own methods like
- get_sms_campaign_candidate_ids_and_phone_numbers()
- create_activity()
- create_sms_campaign_blast()
- send_sms() etc.
"""

# Module Specific
from sms_campaign_service import logger
from sms_campaign_service.config import REDIRECT_URL
from sms_campaign_service.common.models.user import UserPhone
from sms_campaign_service.common.models.misc import UrlConversion
from sms_campaign_service.common.utils.campaign_utils import CampaignBase
from sms_campaign_service.utilities import TwilioSMS, search_link_in_text, url_conversion


class SmsCampaignBase(CampaignBase):

    def __init__(self,  *args, **kwargs):
        super(SmsCampaignBase, self).__init__(*args, **kwargs)
        user_phone = UserPhone.get_by_user_id(self.user_id)
        self.user_phone_value = user_phone.value
        self.shorted_body_text = None

    @staticmethod
    def save(self, form_data):
        """
        This saves the campaign in database table sms_campaign
        :return:
        """
        campaign_data = self.get_campaign_data(form_data)
        pass

    @staticmethod
    def get_campaign_data(self):
        """
        This will get the data from the UI for sms campaign.
        :return:
        """
        pass

    def process_send(self):
        """
        This does the following steps to send campaign to candidates.

        1- Get selected smart lists for the campaign to be sent from sms_campaign_smart_list.
        2- Transform the body text to be sent in sms, add entry in
                url_conversion and sms_campaign_url_conversion db tables.
        3- Loop over all the smart lists and do the followings:

            3-1 Get candidate IDs and candidate phone number(s) to which we need to send the sms.
            3-2- Create sms campaign blast
            3-3- Loop over list of candidate_ids found in step-3-1 and do the followings:

                3-3-1- Send sms
                3-3-2- Create sms campaign send
                3-3-3- Update sms campaign blast
                3-3-4- Add activity (%(candidate_name)s received sms of campaign %(campaign_name)s")
            3-4- Add activity (Campaign %(name)s was sent to %(num_candidates)s candidates")
        :return:
        """
        pass

    def get_candidate_ids_and_phones(self, campaign, user,
                                     new_candidates_only=False):
        """
        For a given smart list,here we get the candidate ids and their phone numbers.

        :param campaign:    sms campaign row
        :param user:        user row
        :return:            Returns array of candidate IDs in the campaign's smart_lists.
                            Is unique.
        """

        # Get smart_lists of this campaign
        smart_lists = self.get_smart_lists_from_campaign()

        # # Get candidate ids
        # # TODO use collections.Counter class for this
        # candidate_ids_dict = dict()  # Store in hash to avoid duplicate candidate ids
        # for smart_list in smart_lists:
        #     # If the campaign is a subscription campaign,
        #     # only get candidates subscribed to the campaign's frequency
        #     if campaign.isSubscription:
        #         campaign_frequency_id = campaign.frequencyId
        #         subscribed_candidate_id_rows = db(
        #             (db.candidate_subscription_preference.frequencyId == campaign_frequency_id) &
        #             (db.candidate_subscription_preference.candidateId == db.candidate.id) &
        #             (db.candidate.ownerUserId == db.user.id) &
        #             (db.user.domainId == user.domainId)
        #         ).select(db.candidate.id, cacheable=True)
        #         candidate_ids = [row.id for row in subscribed_candidate_id_rows]
        #         if not candidate_ids:
        #             logger.error("No candidates in subscription campaign %s", campaign)
        #     else:
        #         # Otherwise, just filter out unsubscribed candidates:
        #         # their subscription preference's frequencyId is NULL, which means 'Never'
        #         candidate_ids = TalentSmartListAPI.get_candidates(smart_list, candidate_ids_only=True)['candidate_ids']
        #         print "candidate_ids: " + str(candidate_ids)
        #         unsubscribed_candidate_ids = []
        #         for candidate_id in candidate_ids:
        #             campaign_subscription_preference = get_subscription_preference(candidate_id)
        #             print "campaign_subscription_preference: " + str(campaign_subscription_preference)
        #             if campaign_subscription_preference and not campaign_subscription_preference.frequencyId:
        #                 unsubscribed_candidate_ids.append(candidate_id)
        #         for unsubscribed_candidate_id in unsubscribed_candidate_ids:
        #             if unsubscribed_candidate_id in candidate_ids:
        #                 candidate_ids.remove(unsubscribed_candidate_id)
        #
        #     # If only getting candidates that haven't been emailed before...
        #     if new_candidates_only:
        #         emailed_candidate_ids_dict = db(
        #             (db.email_campaign_send.emailCampaignId == campaign.id)
        #         ).select(db.email_campaign_send.candidateId, groupby=db.email_campaign_send.candidateId).as_dict(
        #             'candidateId')
        #         for candidate_id in candidate_ids:
        #             if not candidate_ids_dict.get(candidate_id) and not emailed_candidate_ids_dict.get(candidate_id):
        #                 candidate_ids_dict[candidate_id] = True
        #     else:
        #         for candidate_id in candidate_ids:
        #             if not candidate_ids_dict.get(candidate_id):
        #                 candidate_ids_dict[candidate_id] = True
        #
        # unique_candidate_ids = candidate_ids_dict.keys()
        # # Get emails
        # candidate_email_rows = db(
        #     (db.candidate_email.candidateId.belongs(unique_candidate_ids))
        # ).select(db.candidate_email.address, db.candidate_email.candidateId,
        #          groupby=db.candidate_email.address)
        #
        # # array of (candidate id, email address) tuples
        # return [(row.candidateId, row.address) for row in candidate_email_rows]

    def get_smart_lists_from_campaign(self):
        """
        This gives the smart lists relating to a given campaign.
        :return: smart list candidates
        :rtype: list
        """
        user_id = self.user_id
        campaign_id = self.campaign_id
        pass

    def get_sms_campaign_candidate_ids_and_phones(self, smart_list_id):
        """
        This will get the candidates associated to a provided smart list and their
        phone numbers.
        :return:
        """
        pass

    def create_activity(self):
        pass

    def create_or_update_sms_campaign_blast(self):
        pass

    def create_or_update_sms_campaign_send(self):
        pass

    def send_sms(self, candidate_phone_value):
        """
        This uses Twilio API to send sms to a given phone number of candidate
        :return:
        """
        twilio_obj = TwilioSMS()
        twilio_obj.send_sms(body_text=self.shorted_body_text,
                            sender_phone=self.user_phone_value,
                            receiver_phone=candidate_phone_value)

    def process_link_in_body_text(self):
        """
        - Once we have the body text of sms to be sent via sms campaign,
            we check if it contains any link in it.
            If it has any link, we do the followings:

                1- Save that link in db table "url_conversion".
                2- Checks if the db record has source url or not. If it has no source url,
                   we convert the url(to redirect to our app) into shortened url and update
                   the db record. Otherwise we move on to transform body text.
                3. Replace the link in original body text with the shortened url
                    (which we created in step 2)
                4. Return the updated body text

            Otherwise we save the body text in self.shorted_body_text
        """
        link_in_body_text = search_link_in_text(self.body_text)
        if len(link_in_body_text) == 1:
            # We have only one link in body text which needs to shortened.
            url_conversion_id = self.save_or_update_url_conversion(link_in_body_text[0])
            url_conversion_record = UrlConversion.get_by_id(url_conversion_id)
            if not url_conversion_record.source_url:
                short_url, long_url = url_conversion(REDIRECT_URL + '?url_id=%s' % url_conversion_id)
                self.save_or_update_url_conversion(link_in_body_text[0], source_url=short_url)
            else:
                short_url = url_conversion_record.source_url
            self.shorted_body_text = self.transform_body_text(self.body_text,
                                                              link_in_body_text[0],
                                                              short_url)
        elif len(link_in_body_text) > 1:
            # Got multiple links in body text
            logger.info('Got %s links in body text. Body text is %s'
                        % (len(link_in_body_text), self.body_text))
        else:
            # No link is present in body text
            self.shorted_body_text = self.body_text

    @staticmethod
    def transform_body_text(body_text, link_in_body_text, short_url):
        """
        - This replaces the url provided in body text with the shortened url
            to be sent via sms campaign.
        :param body_text: body text to be sent in sms campaign
        :param link_in_body_text: link present in body text
        :param short_url: shortened url
        :type body_text: str
        :type short_url: str
        :return: transformed body text to be sent via sms campaign
        :rtype: str
        """
        text_split = body_text.split(' ')
        index = 0
        for word in text_split:
            if word == link_in_body_text:
                text_split[index] = short_url
                break
            index += 1
        return ' '.join(text_split)

    @staticmethod
    def save_or_update_url_conversion(link_in_body_text, source_url=None):
        """
        - Here we save the url(provided in body text) and the shortened url
            to redirect to our endpoint in db table "url_conversion".
        :param link_in_body_text: link present in body text
        :param source_url: shortened url of the link present in body text
        :type link_in_body_text: str
        :type source_url: str
        :return: id of the record in database
        :rtype: int
        """
        data = {'destination_url': link_in_body_text}
        data.update({'source_url': source_url}) if source_url else ''
        record_in_db = UrlConversion.get_by_destination_url(link_in_body_text)
        if record_in_db:
            record_in_db.update(**data)
            url_record_id = record_in_db.id
        else:
            new_record = UrlConversion(**data)
            UrlConversion.save(new_record)
            url_record_id = new_record.id
        return url_record_id
