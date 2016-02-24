from candidate_service.candidate_app import app
from candidate_service.common.talent_config_manager import TalentConfigKeys

ONE_SIGNAL_APP_ID = app.config[TalentConfigKeys.ONE_SIGNAL_APP_ID]
ONE_SIGNAL_REST_API_KEY = app.config[TalentConfigKeys.ONE_SIGNAL_REST_API_KEY]
PUSH_DEVICE_ID = app.config[TalentConfigKeys.PUSH_DEVICE_ID]