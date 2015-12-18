from flask import Flask
from flask import render_template, request
import json
from one_signal_sdk import OneSignalSdk

one_signal_client = OneSignalSdk(app_id="0847b2c8-8bcd-4196-b755-11fc6869a0e8",
                                 rest_key="ZjYzZjY5ZmMtZTJkMC00OWEzLTk2OWMtNzgwYjcyNzAyMDVj")
app = Flask(__name__, static_url_path='')


@app.route("/")
def show_index():
    return render_template('index.html')


@app.route("/onesignal")
def onesignal():
    return render_template('onesignal.html')


@app.route('/send', methods=['GET', 'POST'])
def send():
    # url =  'https://onesignal.com/api/v1/notifications'
    # header = {"Content-Type": "application/json",
    #           "Authorization": "Basic ZjYzZjY5ZmMtZTJkMC00OWEzLTk2OWMtNzgwYjcyNzAyMDVj"}
    #
    # payload = {"app_id": "0847b2c8-8bcd-4196-b755-11fc6869a0e8",
    #            "included_segments": ["All"],
    #            # "excluded_segments": ["notification1"],
    #            "tags": [{"key": "notification1", "relation": ">", "value": "124"}],
    #            "contents": {"en": "English Message"},
    #            "url": "https://www.google.com",
    #            "chrome_web_icon": "http://cdn.designcrowd.com.s3.amazonaws.com/blog/Oct2012/52-Startup-Logos-2012/SLR_0040_gettalent.jpg"
    #            }
    #
    # req = requests.post(url, headers=header, data=json.dumps(payload))
    #
    # print(req.status_code, req.reason)
    data = request.values
    req = one_signal_client.create_notification(data['url'], data['message'], data['title'])
    if req.ok:
        return req.content
    else:
        return {"error": "Unable to send notification"}
