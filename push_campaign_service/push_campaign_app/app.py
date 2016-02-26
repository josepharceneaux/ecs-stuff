from flask import render_template
from push_campaign_service.push_campaign_app import app
from api.v1_push_campaign_api import push_notification_blueprint

app.register_blueprint(push_notification_blueprint)


@app.route("/")
def index():
    return render_template('index.html')
