__author__ = 'erikfarmer'

import os

from flask.ext.script import Manager
from flask import url_for

from widget_app import app
from widget_app.flask_scripts.db import fill_db
from widget_app.flask_scripts.db import destroy_db
from widget_app.flask_scripts.url_encode import encode_domain_ids
from widget_app.flask_scripts.url_encode import encode_widget_ids

manager = Manager(app)

if not os.getenv('GT_ENVIRONMENT') == 'dev':
    raise Exception("Environment variable GT_ENVIRONMENT detecting non dev environment.")


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


@manager.command
def get_encoded_domains():
    encode_domain_ids()


@manager.command
def get_encoded_widgets():
    encode_widget_ids()


if __name__ == "__main__":
    manager.run()
