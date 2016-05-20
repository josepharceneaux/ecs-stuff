from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from app_common.common.models.db import db

from app_common.common.talent_config_manager import load_gettalent_config
from app_common.common.talent_flask import TalentFlask

app = TalentFlask(__name__)
load_gettalent_config(app.config)

db.init_app(app)
db.app = app

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    manager.run()
