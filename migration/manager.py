from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from auth_service.oauth import app
from auth_service.models.db import db


migrate = Migrate(app=app, db=db)

manager = Manager(app=app)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
