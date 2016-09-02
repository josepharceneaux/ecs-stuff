# TODO: 1- Add init.py as talentbot_service/talentbot_api/__init__.py . See examples from other services.
# TODO: Use init_talent_app() function.
# TODO: 2- Add symlink of common in your service
# TODO: 3- Need to use logger instead of print statements.
# TODO: 4- I think we now need to use SQLAlchemy methods rather than raw queries.

# TODO: Add module level doc string. For any example you can look into any other service.
# TODO: Make sections of import like Standard Library, Third Party, Application Specific
# TODO: Remove unused imports
import os

from talentbot import talentbot, get_bot_id, set_bot_state_active
import views

if __name__ == '__main__':
    # TODO: Kindly add your service in app_common/common/routes.py and import port from there
    # TODO: Also add runserver.py in .idea/runConfigurations so that it will be available in drop down as we have
    # TODO: for other services
    port = int(os.environ.get("PORT", 5000))
    set_bot_state_active()
    talentbot.run(threaded=True, host='0.0.0.0', port=port)
