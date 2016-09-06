BOT_NAME = "talentbot"
AT_BOT = ""
READ_WEB_SOCKET_DELAY = 1
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
TWILIO_NUMBER = "+12015617985"
FACEBOOK_MESSAGE_LIMIT = 319
FACEBOOK_MESSAGE_SPLIT_COUNT = 200
TEXT_MESSAGE_MAX_LENGTH = 152
STANDARD_MSG_LENGTH = 160
MAILGUN_SENDING_ENDPOINT = "https://api.mailgun.net/v3/sandbox59cbb160934f43d7839e1788604c2c06." \
                           "mailgun.org/messages"
MAILGUN_FROM = "TalentBot <postmaster@sandbox59cbb160934f43d7839e1788604c2c06.mailgun.org>"
# TODO: I think dict() would be more readable, we'll access questions with their names(keys)
QUESTIONS = ['how many users are with domain', 'how many candidates with skills',
             'how many candidates from zipcode', 'what is the top performing email campaign from',
             'How many candidate leads did x import into the y talent pool last month', 'what is your name'
             , 'hint']
# TODO: I think dict() would be more readable, we'll access messages from their names(keys)
POSITIVE_MESSAGES = ['hmmmm', 'ok', 'fine', 'whatever', 'yeah', 'ahan', 'so so']
BEST_QUESTION_MATCH_RATIO = 95
FACEBOOK_API_URI = "https://graph.facebook.com/v2.6/me/messages"
