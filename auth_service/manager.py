from flask.ext.script import Shell, Manager
from auth_service.oauth import app, db
from common import models


manager = Manager(app=app)

def make_shell_context():
    return dict(app=app, db=db, models=models)
manager.add_command("Shell", Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()

