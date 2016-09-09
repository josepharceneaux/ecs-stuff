"""
This module contains class EmailBot which is inherited from TalentBot class. It handles bot interaction
with Email.
- authenticate_user()
- reply()
- handle_communication()
"""
# Builtin imports
import random
# Common utils
from talentbot_service.common.models.user import TalentbotAuth
# App specific imports
from talentbot_service.modules.constants import MAILGUN_FROM, AUTHENTICATION_FAILURE_MSG
from talentbot_service.modules.talent_bot import TalentBot
# 3rd party import
import requests


class EmailBot(TalentBot):
    """
    This class handles bot-user communication through Email
    """
    def __init__(self, mailgun_api_key, mailgun_sending_endpoint, questions, bot_name,
                 bot_image, error_messages):
        super(EmailBot, self).__init__(questions, bot_name, error_messages)
        self.mailgun_api_key = mailgun_api_key
        self.mailgun_sending_endpoint = mailgun_sending_endpoint
        self.bot_image = bot_image

    def authenticate_user(self, email_id, subject, email_body):
        """
        Authenticates user and remove secret email token from message body
        :param str email_id: User Email Id
        :param str subject: Received Email subject
        :param str email_body: Received Email body
        :return: tuple (True|False, str|None)
        """
        secret_email_token = TalentbotAuth.query.with_entities(TalentbotAuth.email_secret_token).\
            filter_by(email=email_id).first()
        if secret_email_token:
            if secret_email_token[0] in email_body or secret_email_token[0] in subject:
                # removing secret email token from msg
                email_body = email_body.replace(secret_email_token[0], '')
                return True, email_body
        return False, None

    def reply(self, recipient, subject, message, sender):
        """
        Sends Email to the recipient via mailgun API
        :param str recipient: Email sender
        :param str subject: Subject of email
        :param str message: Email response message
        :param str sender: Email will be sent from this email_id
        :return: response from mailgun API
        """
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
        is_authenticated, message = self.authenticate_user(recipient, subject, message)
        if is_authenticated:
            try:
                response_generated = self.parse_message(message)
                self.reply(recipient, subject, "<br />".join(response_generated.split("\n")), MAILGUN_FROM)
            except (IndexError, NameError, KeyError):
                error_response = random.choice(self.error_messages)
                self.reply(recipient, subject, error_response, MAILGUN_FROM)
        else:  # User not authenticated
            self.reply(AUTHENTICATION_FAILURE_MSG, recipient)

