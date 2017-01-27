"""
This module is the entry point to the Talentbot service
"""
# Common utils
from talentbot_service.common.routes import GTApis
# Service specific
from talentbot_service import app
import talentbot_service.modules.views
from talentbot_service.talentbot_api.talentbot_auth import talentbot_blueprint

if __name__ == '__main__':
    app.register_blueprint(talentbot_blueprint)
    app.run(threaded=True, host='0.0.0.0', port=GTApis.TALENTBOT_PORT)
