# TODO: Kindly rename const.py to constants.py
# TODO: Kindly rename talentbot-service to talentbot_service

BOT_NAME = "talentbot"
AT_BOT = ""
READ_WEB_SOCKET_DELAY = 1
ACCESS_TOKEN = "EAACgOZA0chrgBALk1h0NgkpOcnmjRd6OfgywbZAZBeZBpRCguTDMaLZAauErNDLkXU" \
               "ujcV7ZCExez5DA6gD2ShvaBHz7irQRZBnOGFRqfluUKvlie2d0bhVYS5JUJQgoGwhlSNCQL" \
               "zxS5iK0lQsBSqbCld7Hq6HRLbFwJKvgWLaBwZDZD"
# SQLALCHEMY_DATABASE_URI = 'mysql://root:5683@localhost:3306/talentdb'
# SQLALCHEMY_DATABASE_URI = 'mysql://sql7133744:pGRUGtQ8Ye@sql7.freemysqlhosting.net/sql7133744'
SQLALCHEMY_DATABASE_URI = "mysql://talent_web:s!web976892@stage-db.gettalent.com/talent_staging"
# TODO: I think we should use dict or some better data structure for the sake of readability(while accessing entries)
ERROR_MESSAGE = ['Hmm, I do not know this', 'I will have to ask @kamal about that', 'Sorry I did not get you']
BOT_IMAGE = 'https://d13yacurqjgara.cloudfront.net/users' \
            '/15084/screenshots/702565/attachments/64916/Space_Ghost-iPad---1024x1024.jpg'
GREETINGS = ['hello', 'hey', 'howdy', 'greetings', 'hi']
# TODO: Plural, HINTS
HINT = ['I am Talent Bot @kamal is teaching me new things, right now'
        ' I can answer following questions for you:_\n1- How many users are there with'
        ' domain [domain name]?\n2- How many candidates are there with skills [skills separated with space]?\n'
        '3- How many candidates from zipcode [zipcode]?\n4- What is the top performing email'
        ' campaign from [year]?\n5- How many candidate leads did [user name]'
        ' import into the [talent pool name] talent pool last month?\n*GOOD LUCK*']
OK_RESPONSE = ['hmm', '**nodes**']
<<<<<<< HEAD:talentbot_service/const.py
TWILIO_AUTH_TOKEN = "09e1a6e40b9d6588f8a6050dea6bbd98"
=======

# TODO: Put all the keys in web.cfg (That will require updating TalentConfigKeys() in common/talent_config_manager.py
TWILIO_AUTH_TOKEN = "##################################"
>>>>>>> 5dbd5a4a8295243e7916f6b36a17921ce0fe29b0:talentbot-service/const.py
TWILIO_ACCOUNT_SID = "AC7f332b44c4a2d893d34e6b340dbbf73f"
TWILIO_NUMBER = "+12015617985"
SLACK_BOT_TOKEN = 'xoxb-74113722021-AWVXranhHgyFwz4n0u2izwcY'
FACEBOOK_MESSAGE_LIMIT = 319
FACEBOOK_MESSAGE_SPLIT_COUNT = 200
TEXT_MESSAGE_MAX_LENGTH = 152
STANDARD_MSG_LENGTH = 160
MAILGUN_SENDING_ENDPOINT = "https://api.mailgun.net/v3/sandbox59cbb160934f43d7839e1788604c2c06." \
                           "mailgun.org/messages"
MAILGUN_API_KEY = "key-c84dc16ab8c908fa4ab6a9f05862a1cc"
MAILGUN_FROM = "TalentBot <mailgun@sandbox59cbb160934f43d7839e1788604c2c06.mailgun.org>"
# TODO: I think dict() would be more readable, we'll access questions with their names(keys)
QUESTIONS = ['how many users are with domain', 'how many candidates with skills',
             'how many candidates from zipcode', 'what is the top performing email campaign from',
<<<<<<< HEAD:talentbot_service/const.py
             'How many candidate leads did x import into the y talent pool last month', 'what is your name']
=======
             'How many candidate leads did import into the talent pool last month', 'what is your name']
# TODO: I think dict() would be more readable, we'll access messages from their names(keys)
>>>>>>> 5dbd5a4a8295243e7916f6b36a17921ce0fe29b0:talentbot-service/const.py
POSITIVE_MESSAGES = ['hmmmm', 'ok', 'fine', 'whatever', 'yeah', 'ahan', 'so so']
BEST_QUESTION_MATCH_RATIO = 95
