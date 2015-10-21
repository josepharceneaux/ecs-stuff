__author__ = 'erikfarmer'

import os
os.environ['GT_ENVIRONMENT'] = 'dev'

from flask.ext.script import Manager
from flask import url_for

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


@manager.command
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    for line in sorted(output):
        print line


if __name__ == "__main__":
    manager.run()