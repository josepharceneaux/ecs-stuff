# Third Party
import twilio
import twilio.rest

# Application Specific
from config import TWILIO_ACCOUNT_SID
from config import TWILIO_AUTH_TOKEN

try:
    client = twilio.rest.TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body="Hello World",
        to="+923344955479",
        from_="+18312221043"
    )
except twilio.TwilioRestException as e:
    print e
