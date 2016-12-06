"""
This module contains celery tasks for talentbot service
*-----------------------------Only Facebook and Slack Celery Tasks---------------------------------*
We are creating celery tasks for Facebook and Slack only because callbacks from Twilio and AWS-SES can wait for enough
time.
But callbacks from Facebook waits fo 5 secs and from Slack waits for 3 secs after that they initiate another callback,
So we return a "200 OK" response to Slack and Facebook right away and run their corresponding handlers asynchronously
as Celery tasks
====================================================================================================
"""
# Service Specific
from talentbot_service import celery_app as celery
from talentbot_service.modules.constants import QUESTIONS, BOT_NAME, ERROR_MESSAGE
from talentbot_service.modules.facebook_bot import FacebookBot
from talentbot_service.modules.slack_bot import SlackBot

slack_bot = SlackBot(QUESTIONS, BOT_NAME, ERROR_MESSAGE)
facebook_bot = FacebookBot(QUESTIONS, BOT_NAME, ERROR_MESSAGE)


@celery.task(name="run_slack_communication_handler")
def run_slack_communication_handler(channel_id, message, slack_user_id, current_timestamp):
        """
        This method runs class SlackBot's handle_communication() method as a celery task
        :param string channel_id: Slack channel Id
        :param string message: User's message
        :param string slack_user_id: User's Slack Id
        :param string current_timestamp: Current timestamp
        """
        slack_bot.handle_communication(channel_id, message, slack_user_id, current_timestamp)


@celery.task(name="run_facebook_communication_handler")
def run_facebook_communication_handler(fb_user_id, message):
        """
        This method runs class FacebookBot's handle_communication() method as a celery task
        :param string fb_user_id: User's Facebook Id
        :param string message: User's message
        :rtype: None
        """
        facebook_bot.handle_communication(fb_user_id, message)
