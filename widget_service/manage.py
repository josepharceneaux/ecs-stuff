__author__ = 'erikfarmer'

import os
os.environ['GT_ENVIRONMENT'] = 'dev'

from flask.ext.script import Manager

from widget_app import app
from widget_app.flask_scripts.db import fill_db
from widget_app.flask_scripts.db import destroy_db

manager = Manager(app)


@manager.command
def seed_server():
    print 'Initializing dev-server seed'
    fill_db()
    print 'Finished creating database data for /test/<widget> endpoint'


@manager.command
def unseed_server():
    print 'Initializing dev-server seed reap'
    destroy_db()
    print 'Finished emptying database'


if __name__ == "__main__":
    manager.run()