"""
This module contains class EmailBot which is inherited from TalentBot class. It handles bot interaction
with Email.
- authenticate_user()
- reply()
- handle_communication()
"""
# Builtin imports
import random
import requests
# App specific imports
from talentbot_service.modules.constants import MAILGUN_FROM
from talentbot_service.modules.talent_bot import TalentBot


class EmailBot(TalentBot):
    def __init__(self, mailgun_api_key, mailgun_sending_endpoint, questions, bot_name,
                 bot_image, error_messages):
        TalentBot.__init__(self, questions, bot_name, error_messages)
        self.mailgun_api_key = mailgun_api_key
        self.mailgun_sending_endpoint = mailgun_sending_endpoint
        self.bot_image = bot_image

    def authenticate_user(self):
        """
        Authenticates user
        :return: True|False
        """
        return True

    def reply(self, recipient, subject, message, sender):
        """
        Sends Email to the recipient via mailgun API
        :param str recipient: Email sender
        :param str subject: Subject of email
        :param str message: Email response message
        :param str sender: Email will be sent from this email_id
        :return: response
        """
        # TODO: we are using Amazon SES to send emails currently. Maybe we can use that.
        html = '<html><img src="' + self.bot_image + '" style="width: 9%; display:'\
                                                     ' inline;"><h5 style="display:'\
                                                     ' table-cell; vertical-align:'\
                                                     ' top;margin-left: 1%;">' + message +\
               '</h5></html>'
        response = requests.post(self.mailgun_sending_endpoint, auth=("api", self.mailgun_api_key),
                                 data={"from": sender, "to": recipient, "subject": subject,
                                       "html": html
                                       })
        return response

    def handle_communication(self, recipient, subject, message):
        """
        Handles communication between user and bot
        :param str recipient: User's email Id
        :param str subject: Email subject
        :param message: User's message
        """
        try:
            response_generated = self.parse_message(message)
            self.reply(recipient, subject, "<br />".join(response_generated.split("\n")), MAILGUN_FROM)
        except (IndexError, NameError, KeyError):
            error_response = random.choice(self.error_messages)
            self.reply(recipient, subject, error_response, MAILGUN_FROM)
