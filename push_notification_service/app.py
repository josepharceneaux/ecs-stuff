from flask import render_template, request

from push_notification_service import init_push_notification_app

app = init_push_notification_app()

from push_notification_service.rest_api.v1_push_notification_api import push_notification_blueprint

app.register_blueprint(push_notification_blueprint)


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/send', methods=['GET', 'POST'])
def send():
    data = request.get_json()
    players = data.get('players')
    req = one_signal_client.create_notification(data['url'], data['message'], data['title'], players=players)
    if req.ok:
        return req.content
    else:
        return {"error": "Unable to send notification"}
