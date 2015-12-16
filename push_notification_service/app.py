from flask import Flask
from flask import render_template
import requests
import json
app = Flask(__name__, static_url_path='')


@app.route("/")
def show_index():
    return render_template('index.html')


@app.route("/roost")
def roost():
    return render_template('roost.html')


@app.route("/onesignal")
def onesignal():
    return render_template('onesignal.html')


@app.route('/onesignal/push')
def onesignal_push():
    url =  'https://onesignal.com/api/v1/notifications'
    header = {"Content-Type": "application/json",
              "Authorization": "Basic ZjYzZjY5ZmMtZTJkMC00OWEzLTk2OWMtNzgwYjcyNzAyMDVj"}

    payload = {"app_id": "0847b2c8-8bcd-4196-b755-11fc6869a0e8",
               "included_segments": ["notification1"],
               "contents": {"en": "English Message"},
               "url": "https://www.google.com",
               "chrome_web_icon": "http://cdn.designcrowd.com.s3.amazonaws.com/blog/Oct2012/52-Startup-Logos-2012/SLR_0040_gettalent.jpg"
               }

    req = requests.post(url, headers=header, data=json.dumps(payload))

    print(req.status_code, req.reason)
    return req.content


@app.route('/roost/push')
def roost_push():
    url = "https://go.goroost.com/api/push"
    data = {'alert': 'How are you? I am roost.', 'url':'https://getbootstrap.com'}

    headers = {'Content-type': 'application/json'}

    r = requests.post(url, json=data, headers=headers, auth=('y654irhu7xre1a9nwagu5jc326x436nh',
                                                             'kqu5oom8yvxy37wlrlf0b7zlm2373y8h'))
    return r.content
