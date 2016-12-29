"""
This module contains UserStateHandler class which handles the user state in redis
 - empty_user_state()
"""
from talentbot_service.common.redis_cache import redis_store
from talentbot_service.common.models.user import UserPhone, TalentbotAuth
from talentbot_service import logger


class UserStateHandler(object):
    def __init__(self):
        pass

    @staticmethod
    def empty_users_state():
        """
        This method removes saved users' states from redis db to avoid deadlocks
        """
        logger.info("Flushing user states saved in redis")
        # Getting registered user phone ids
        user_phone_ids = TalentbotAuth.get_all_user_phone_ids()
        # Getting first entry of tuples
        user_phone_ids = list(*zip(*user_phone_ids))
        """
        If there is no user_phone_id available in table we get [None], that's why I'm
        comparing user_phone_ids[0] instead of user_phone_ids because [None] != []
        """
        if user_phone_ids[0]:
            # Getting user ids against registered users' phone ids
            user_ids = UserPhone.get_user_ids_by_phone_ids(user_phone_ids)
            # Extracting data from tuple
            user_ids = list(*zip(*user_ids))
            for user_id in user_ids:
                redis_store.delete("bot-pg-%d" % user_id)
