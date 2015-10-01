import os
from gt_common.models.config import GTSQLAlchemy
if not GTSQLAlchemy.db_session:
    app_cfg = os.path.abspath('app.cfg')
    logging_cfg = os.path.abspath('logging.conf')

    GTSQLAlchemy(app_config_path=app_cfg,
                 logging_config_path=logging_cfg)
from app.app import app

if __name__ == '__main__':
    # TODO Have to remove this, only here for testing purposes
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(port=5000, debug=True)
