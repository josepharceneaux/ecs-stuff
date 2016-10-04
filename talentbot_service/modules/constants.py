"""
This script contains Talentbot constants
"""
from talentbot_service.common.models.sms_campaign import SmsCampaignBlast
from talentbot_service.common.models.email_campaign import EmailCampaignBlast
from talentbot_service.common.models.push_campaign import PushCampaignBlast
BOT_NAME = "talentbot"
AT_BOT = ""
READ_WEB_SOCKET_DELAY = 1
ERROR_MESSAGE = ['Hmm, I do not know this', 'I will have to ask @kamal about that',
                 'Sorry I did not get you']
# Bot image's web-link
BOT_IMAGE = 'https://d13yacurqjgara.cloudfront.net/users' \
            '/15084/screenshots/702565/attachments/64916/Space_Ghost-iPad---1024x1024.jpg'
GREETINGS = ['hello', 'hey', 'howdy', 'greetings', 'hi']
HINT = '''I am Talent Bot @kamal is teaching me new things, right now I can answer following questions for you:_
1- How many users are there in my domain?
2- How many candidates are there with skills [skills separated with space]?
3- How many candidates from zipcode [zipcode]?
4- What is the top performing [x] campaign from [year]?
5- How many candidate leads did [user name] import into the [talent pool name] talent pool in last n months?
*GOOD LUCK*'''
OK_RESPONSE = ['hmm', '**nodes**']
TWILIO_NUMBER = "+12015617985"
FACEBOOK_MESSAGE_LIMIT = 319
FACEBOOK_MESSAGE_SPLIT_COUNT = 200
TEXT_MESSAGE_MAX_LENGTH = 152
STANDARD_MSG_LENGTH = 160
MAILGUN_SENDING_ENDPOINT = "https://api.mailgun.net/v3/sandbox59cbb160934f43d7839e1788604c2c06." \
                           "mailgun.org/messages"
MAILGUN_FROM = "TalentBot <postmaster@sandbox59cbb160934f43d7839e1788604c2c06.mailgun.org>"
QUESTIONS = ['how many users are in my domain', 'how many candidates are there with skills',
             'how many candidates from zipcode',
             'what is the top performing campaign from',
             'How many candidate leads did x import into the y talent pool last',
             'what is your name', 'hint', 'help', 'what are your features', 'what can you do',
             'tell me the number of users in my domain', 'how many users exist in my domain',
             'how many candidates know', 'candidates who know',
             'number of candidates who has grasp on', 'candidates having skills',
             'tell me the number of candidates who has mastered in skills',
             'which were the top performing email campaign last',
             'show me the top email sms push campaigns from', 'how many candidates added into the talent pool last',
             'candidates who has grasp on', 'candidates having grasp on',
             'tell me the number of candidates from zipcode', 'candidates with skills',
             'what is the top performing email campaign from last', 'what is the top performing sms campaign from last',
             'what is the top performing push campaign from last', 'which was the top smsemailpush campaign last',
             'how many candidates are there in my domain', 'candidates in my domain', 'how many candidates has grasp on']
POSITIVE_MESSAGES = ['hmmmm', 'ok', 'fine', 'whatever', 'yeah', 'ahan', 'so so']
BEST_QUESTION_MATCH_RATIO = 95
FACEBOOK_API_URI = "https://graph.facebook.com/v2.6/me/messages"
AUTHENTICATION_FAILURE_MSG = 'Sorry you are not registered to use this service\n' \
                            'Go to the http://www.gettalent.com to register yourself'
SLACK_AUTH_URI = 'https://slack.com/api/oauth.access'
CAMPAIGN_TYPES = {'sms': SmsCampaignBlast.top_performing_sms_campaign,
                  'email': EmailCampaignBlast.top_performing_email_campaign,
                  'push': PushCampaignBlast.top_performing_push_campaign}
# TODO: Remove this when we move to prod
TWILIO_AUTH_TOKEN = "09e1a6e40b9d6588f8a6050dea6bbd98"
TWILIO_ACCOUNT_SID = "AC7f332b44c4a2d893d34e6b340dbbf73f"
