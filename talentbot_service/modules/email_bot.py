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
from talentbot_service.modules.constants import AUTHENTICATION_FAILURE_MSG, SOURCE_EMAIL_ADDRESS
from talentbot_service.modules.talent_bot import TalentBot
from talentbot_service import logger
from talentbot_service.common.utils.amazon_ses import send_email


class EmailBot(TalentBot):
    """
    This class handles bot-user communication through Email
    """
    def __init__(self, questions, bot_name,
                 bot_image, error_messages):
        super(EmailBot, self).__init__(questions, bot_name, error_messages)
        self.bot_image = bot_image

    def authenticate_user(self, email_id, subject, email_body):
        """
        Authenticates user and remove secret email token from message body
        :param str email_id: User Email Id
        :param str subject: Received Email subject
        :param str email_body: Received Email body
        :rtype: tuple (True|False, str|None, int|None)
        """
        user_id = TalentbotAuth.get_user_id(email=email_id)
        if user_id:
            return True, email_body, user_id[0]
        return False, None, None

    def reply(self, recipient, subject, message):
        """
        Sends Email to the recipient via mailgun API
        :param str recipient: Email sender
        :param str subject: Subject of email
        :param str message: Email response message
        :return: response from mailgun API
        :rtype: response
        """
        html = '<html><img src="' + self.bot_image + '" style="width: 9%; display:'\
                                                     ' inline;"><h5 style="display:'\
                                                     ' table-cell; vertical-align:'\
                                                     ' top;margin-left: 1%;">' + message +\
               '</h5></html>'
        response = send_email(source=SOURCE_EMAIL_ADDRESS, subject=subject, body=None, html_body=html,
                              email_format='html', to_addresses=[recipient])
        logger.info('Mail reply "%s", to %s' % (message, recipient))
        return response

    def handle_communication(self, recipient, subject, message):
        """
        Handles communication between user and bot
        :param str recipient: User's email Id
        :param str subject: Email subject
        :param message: User's message
        :rtype: None
        """
        is_authenticated, message, user_id = self.authenticate_user(recipient, subject, message)
        if is_authenticated:
            try:
                response_generated = self.parse_message(message, user_id)
                if not response_generated:
                    raise IndexError
                response_generated = self.clean_response_message(response_generated)
                self.reply(recipient, subject, "<br />".join(response_generated.split("\n")))
            except (IndexError, NameError, KeyError):
                error_response = random.choice(self.error_messages)
                self.reply(recipient, subject, error_response)
        else:  # User not authenticated
            self.reply(recipient, subject, AUTHENTICATION_FAILURE_MSG)

