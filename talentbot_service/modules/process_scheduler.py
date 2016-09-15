"""
This module has a class ProcessScheduler which runs class SlackBot's question handler in a thread and
makes sure it is finished.
 - schedule_process()
"""
# Builtin imports
from multiprocessing import Process
# Service specific imports
from talentbot_service import logger
from talentbot_service.modules.constants import PROCESS_MAX_TIME


class ProcessScheduler(object):
    """
    This class runs class SlackBot's handle_question() method in an async thread
    """
    def __init__(self):
        pass

    @staticmethod
    def schedule_process(slack_bot, channel_id, message, slack_user_id, current_timestamp):
        """
        This method runs class SlackBot's handle_question() method in a thread and makes sure it ends
        :param SlackBot slack_bot: SlackBot object
        :param str channel_id: Slack channel Id
        :param str message: User's message
        :param str slack_user_id: User's Slack Id
        :param str current_timestamp: Current timestamp
        """
        process = Process(target=slack_bot.handle_communication,
                          args=(channel_id, message, slack_user_id, current_timestamp))
        process.start()
        process.join(PROCESS_MAX_TIME)
        if process.is_alive():
            logger.info("Killing process: %s" % process.pid)
            process.terminate()
