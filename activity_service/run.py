
__author__ = 'Erik Farmer'

from activities_app import app
from flask.ext.common.common.routes import GTApis


if __name__ == '__main__':
    app.run(port=GTApis.ACTIVITY_SERVICE_PORT, debug=True)
