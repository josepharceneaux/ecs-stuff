from graphql_service.common.utils.models_utils import init_talent_app
from graphql_service.common.models.db import db
from graphql_service.common.talent_config_manager import TalentConfigKeys

app, logger = init_talent_app(__name__)

try:
    db.create_all()
    db.session.commit()
except Exception as e:
    logger.exception("Could not start graphql_service in {env} environment because: {error}".format(
        env=app.config[TalentConfigKeys.ENV_KEY], error=e.message
    ))
