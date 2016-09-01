import os

from talentbot import talentbot, get_bot_id, set_bot_state_active
import views

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    set_bot_state_active()
    talentbot.run(threaded=True, host='0.0.0.0', port=port)
