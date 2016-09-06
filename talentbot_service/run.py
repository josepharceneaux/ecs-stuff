# Builtin imports
import os
# Service specific
from talentbot_service import app
# Common utils
from talentbot_service.common.routes import GTApis
# App specific
import talentbot_service.modules.views

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(threaded=True, host='0.0.0.0', port=GTApis.TALENTBOT_PORT)
