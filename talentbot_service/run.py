"""
This module is the entry point to the Talentbot service
"""
# Common utils
from talentbot_service.common.routes import GTApis
# Service specific
from talentbot_service import app
from modules.user_state_handler import UserStateHandler
import talentbot_service.modules.views

if __name__ == '__main__':

    UserStateHandler.empty_users_state()
    app.run(threaded=True, host='0.0.0.0', port=GTApis.TALENTBOT_PORT)
