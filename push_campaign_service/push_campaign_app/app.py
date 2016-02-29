from flask import render_template
from push_campaign_service.push_campaign_app import app
from api.v1_push_campaign_api import push_notification_blueprint

app.register_blueprint(push_notification_blueprint)

# TODO ; kindly put a detailed comment here as to why index.html can be useful. I am assuming this can
# help the user to test things e.g. by subscribing and etc so a detailed comment can save him a lot of time
@app.route("/")
def index():
    return render_template('index.html')
