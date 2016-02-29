from flask import render_template
from push_campaign_service.push_campaign_app import app
from api.v1_push_campaign_api import push_notification_blueprint

app.register_blueprint(push_notification_blueprint)


@app.route("/")
def index():
    """
    This endpoint is not requirement of service but it helps to do some stuff like
    subscribe , un-subscribe, send a test push notification though our app to a test device.
    :return:
    """
    return render_template('index.html')
