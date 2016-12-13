"""
IT IS NOT PART OF TALENTBOT_SERVICE IT JUST HELPS US TESTING SMS ENDPOINT USING A US NUMBER "+18312221043"
================================================INDEPENDENT SMS TESTING APP=================================
This is an independent test app to test conversation with bot via SMS. It uses +18312221043 number to send
and receive SMS from bot.

*HOW TO USE*
To use this app, just run it locally, expose the endpoints using ngrok and add "http://localhost:5000/receive_message"
as a callback against "+18312221043" on twilio.com.

Use send message endpoint http://localhost:5000/send_message[POST]
with json data:
{
    "text": "YOUR DESIRED QUESTION"
}
It will send this text as an SMS to bot and logs the received message from bot on
http://localhost:5000/receive_message[POST] endpoint
"""
from flask import Flask
from flask import request
from twilio.rest import TwilioRestClient

app = Flask('sms_helper')

TWILIO_AUTH_TOKEN = "09e1a6e40b9d6588f8a6050dea6bbd98"
TWILIO_ACCOUNT_SID = "AC7f332b44c4a2d893d34e6b340dbbf73f"
MY_NUMBER = "+18312221043"
RECIPIENT = "+12015617985"

client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@app.route('/send_message', methods=['POST'])
def send_message():
    text = request.json.get("text")
    message = client.messages.create(to=RECIPIENT, from_=MY_NUMBER, body=text)
    print 'SMS Reply: ' + text
    print 'Twilio response status: ', message.status
    return message.status


@app.route('/receive_message', methods=['POST'])
def receive_message():
    recipient = request.form.get('From')
    message_body = request.form.get('Body')
    print "Message Received from %s: %s" % (recipient, message_body)
    return 'OK'

if __name__ == '__main__':
    app.run()
