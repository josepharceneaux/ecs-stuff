import os

from talentbot import set_bot_state_active
from talentbot_service import app
import views

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    set_bot_state_active()
    app.run(threaded=True, host='0.0.0.0', port=port)
