"""
This is a flask app which listens web hooks from Facebook, Twilio, Mailgun
and Slack, receives the message processes it and generates a response according
to it and replies to specific chanel.
 - get_bot_id()
 - handle_slack_messages()
 - reply_on_slack()
 - append_list_with_spaces()
 - parse_skills()
 - handle_user_messages()
 - create_a_response()
 - get_sqlalchemy_engine()
 - get_db_connection()
 - execute_query()
 - make_a_post_call_to_the_facebook()
 - sender_action()
 - reply_on_facebook()
 - send_mail_via_api
 - get_total_sms_segments()
"""
# Builtin imports
import random
import re
# App specific imports
from const import ACCESS_TOKEN, SQLALCHEMY_DATABASE_URI,\
    ERROR_MESSAGE, BOT_IMAGE, GREETINGS, HINT,\
    OK_RESPONSE, BOT_NAME, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,\
    SLACK_BOT_TOKEN, FACEBOOK_MESSAGE_LIMIT, FACEBOOK_MESSAGE_SPLIT_COUNT,\
    TEXT_MESSAGE_MAX_LENGTH, MAILGUN_SENDING_ENDPOINT, MAILGUN_API_KEY, MAILGUN_FROM
# 3rd party import
import requests
from flask import Flask
from sqlalchemy import create_engine
from twilio.rest import TwilioRestClient
from slackclient import SlackClient

talentbot = Flask(__name__)
twilio_client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
slack_client = SlackClient(SLACK_BOT_TOKEN)
AT_BOT = ""


def set_bot_state_active():
    slack_client.rtm_connect()
    api_call_response = slack_client.api_call("users.setActive")
    print 'bot state is active: ', api_call_response.get('ok')


def get_bot_id():
    """
    Gets bot Id
    """
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print "Bot ID for %s is %s" % (user['name'], user.get('id'))
                global AT_BOT
                AT_BOT = '<@'+user.get('id')+'>'
                return AT_BOT
    print("could not find bot user with the name " + BOT_NAME)


def handle_slack_messages(chanel, message):
    """
    Create a response and replies with it
    :param str chanel: Slack user Id
    :param str message: Message received to bot
    """
    try:
        response = create_a_response(message)
        reply_on_slack(chanel, response)
    except Exception:
        reply_on_slack(chanel, random.choice(ERROR_MESSAGE))


def reply_on_slack(chanel, msg):
    """
    Reply to user on specified slack channel
    :param str chanel: Slack channel
    :param str msg: Message received to bot
    """
    print 'message:', msg
    slack_client.api_call("chat.postMessage", channel=chanel,
                          text=msg, as_user=True)


def append_list_with_spaces(_list):
    """
    Append a list elements with spaces between then
    :param _list: list
    :return: str result
    """
    result = ""
    for element in _list:
        result += element+" "
    return result


def parse_skills(skills_list):
    """
    Converts space separated skills to comma separated skills
    :param list skills_list: List which contains space separated skills
    :return: str parsed_skills
    """
    parsed_skills = '('
    for skill in skills_list:
        temp = '"'+skill.lower()+'"'
        if skills_list.index(skill) < len(skills_list) - 1:
            temp += ','
        parsed_skills += temp
    parsed_skills += ')'
    return parsed_skills


def handle_user_messages(user_id, message):
    """
    Takes user_id and message and makes some function calls
    and make communication happen between bot and user
    :param str user_id: User Id
    :param str message: Received message
    :return: None
    """
    response_message = create_a_response(message)
    if len(response_message) > FACEBOOK_MESSAGE_LIMIT:
        tokens = response_message.split('\n')
        split_response_message = ""
        while len(tokens) > 0:
            while len(split_response_message) < FACEBOOK_MESSAGE_SPLIT_COUNT and len(tokens) > 0:
                split_response_message = split_response_message + tokens.pop(0) + "\n"
            reply_on_facebook(user_id, split_response_message)
            split_response_message = ""
    else:
        reply_on_facebook(user_id, response_message)
    sender_action(user_id, "typing_off")
    return None


def create_a_response(message):
    """
    Generates a response by processing received message
    :param str message: Message received
    :rtype str
    """
    message = message.rstrip('?. ')
    message = message.lstrip(': ')
    message_tokens = re.split(' |,', message)
    if message_tokens[0].lower() in 'okay' or message_tokens[0].lower() \
            in 'hmmmmmm' and len(message_tokens[0]) < 5:
        return random.choice(OK_RESPONSE)
    if message_tokens[0].lower() in 'hints' and len(message_tokens[0]) > 3:
        return HINT[0]
    if message_tokens[0].lower() in GREETINGS:
        return random.choice(GREETINGS)
    if len(message_tokens) > 7 and message_tokens[0].lower() == 'how' and \
            message_tokens[1].lower() == 'many'\
            and message_tokens[6].lower() == 'domain' and message_tokens[7].lower():
        query = 'SELECT COUNT(DISTINCT user.Id) as count from user,domain' \
                ' WHERE user.domainId = domain.Id and lower(domain.Name) = "' + \
                message_tokens[7].lower()+'"'
        result = execute_query(query)
        if result:
            response_message = "Users in domain "+message_tokens[7]+" : "
            for row in result:
                count = row['count']
                response_message += str(count)
            return response_message
    if len(message_tokens) > 7 and (message_tokens[0].lower() in "what's"
                                    or message_tokens[0].lower() in "which's")\
            and message_tokens[1].lower() in ['is', 'the']\
            and message_tokens[-3].lower() in 'campaigns' and message_tokens[-2].lower() == 'from':
        year = message_tokens[-1]
        query = "SELECT MAX( DISTINCT email_campaign_blast.Opens) as max, " \
                "email_campaign_blast.EmailCampaignId as id" \
                ", email_campaign.Name as name " \
                "from email_campaign_blast, email_campaign " \
                "WHERE email_campaign_blast.EmailCampaignId = email_campaign.Id and " \
                "((YEAR(email_campaign_blast.SentTime) = " \
                "'"+year+"') or " \
                "(YEAR(email_campaign_blast.UpdatedTime) =" \
                " '"+year+"')) " \
                "GROUP BY email_campaign_blast.EmailCampaignId, email_campaign.Name " \
                "ORDER BY MAX(email_campaign_blast.Opens) " \
                "DESC " \
                "LIMIT 1"
        result = execute_query(query)
        if result:
            campaign_id = -1
            user_name = ""
            for row in result:
                global campaign_id, user_name
                campaign_id = row['id']
                user_name = row['name']
            if campaign_id != -1 and user_name != "":
                response_message = 'Top performing email campaign from '+year+' is'\
                               ' "%s"' % user_name
            else:
                response_message = "Sorry couldn't find top email campaign from "+year
            return response_message
    if len(message_tokens) > 11 and message_tokens[0].lower() == 'how' \
            and message_tokens[1].lower() == 'many'\
            and message_tokens[2].lower() in 'candidates' and\
            message_tokens[6].lower() in 'import' or message_tokens[5].lower() in 'import':
        talent_index = [message_tokens.index(talent) for talent
                        in message_tokens if 'talent' in talent.lower()][0]
        import_index = [message_tokens.index(_import) for _import
                        in message_tokens if 'import' in _import.lower()][0]
        talent_pool_name = message_tokens[import_index+3:talent_index:]
        user_name = message_tokens[import_index-1]
        spaced_talent_pool_name = append_list_with_spaces(talent_pool_name)
        query = "SELECT COUNT(DISTINCT talent_pool_candidate.candidate_id) as count" \
                " from talent_pool_candidate, talent_pool, user" \
                " where talent_pool_candidate.talent_pool_id = talent_pool.id and" \
                " talent_pool.user_id = user.id and ((YEAR(talent_pool_candidate.added_time) =" \
                " YEAR(CURRENT_DATE - INTERVAL 1 MONTH) AND MONTH(talent_pool_candidate.added_time) = " \
                "MONTH(CURRENT_DATE - INTERVAL 1 MONTH)) or (YEAR(talent_pool_candidate.updated_time) =" \
                " YEAR(CURRENT_DATE - INTERVAL 1 MONTH) AND MONTH(talent_pool_candidate.updated_time) = " \
                "MONTH(CURRENT_DATE - INTERVAL 1 MONTH)))" \
                " and LOWER(user.firstName) = '"+user_name.lower()+"' and LOWER(talent_pool.name) = '"\
                + spaced_talent_pool_name.lower()+"'" \
                " GROUP BY talent_pool.id"
        result = execute_query(query)
        if result:
            response_message = user_name.title()+" added %d candidates in "+spaced_talent_pool_name +\
                               "talent pool last month"
            count = 0
            for row in result:
                global count
                count = row['count']
            response_message = response_message % count
            return response_message
    if len(message_tokens) >= 6 and message_tokens[0].lower() == 'how' \
            and message_tokens[1].lower() == 'many' and 'skill' in message:
        skill_index = [message_tokens.index(skill) for skill
                       in message_tokens if 'skil' in skill.lower()][0]
        parsed_skills = parse_skills(message_tokens[skill_index + 1::])
        query = 'SELECT COUNT(DISTINCT candidate.Id) as count ' \
                'from candidate, candidate_skill WHERE candidate.Id = ' \
                'candidate_skill.CandidateId and lower(candidate_skill.Description)' \
                ' in ' + parsed_skills
        result = execute_query(query)
        if result:
            response_message = "There are %d candidates with skills " + \
                               parsed_skills.strip('("")').replace('","', ' ')
            for row in result:
                count = row['count']
                response_message = response_message % count
                if count == 1:
                    response_message = response_message.replace('are', 'is'). \
                        replace('candidates', 'candidate')
            return response_message
    if len(message_tokens) > 5 and message_tokens[0].lower() == 'how'\
            and message_tokens[1].lower() == 'many' \
            and message_tokens[2].lower() in 'candidates' and 'zipcode' in message:
        zip_index = [message_tokens.index(zipcode) for zipcode
                     in message_tokens if 'zip' in zipcode][0]
        query = 'SELECT COUNT(DISTINCT candidate_address.CandidateId) as count from candidate_address,' \
                ' candidate where candidate_address.CandidateId' \
                ' = candidate.Id and candidate_address.ZipCode = '+message_tokens[zip_index+1]
        result = execute_query(query)
        if result:
            response_message = "Number of candidates from zipcode " +\
                               message_tokens[zip_index + 1] + " : "
            for row in result:
                count = row['count']
                response_message += str(count)
            return response_message
    if len(message_tokens) > 3 and message_tokens[0].lower() in 'what'\
            and message_tokens[1].lower() in 'is' and message_tokens[2].lower() == 'your'\
            and message_tokens[3].lower() == 'name':
        return "My name is "+BOT_NAME
    return random.choice(ERROR_MESSAGE)


def get_sqlalchemy_engine():
    """
    Executes the create engine method and returns the engine object
    :return: sqlalchemy.engine
    """
    return create_engine(SQLALCHEMY_DATABASE_URI)


def get_db_connection():
    """
    Returns db connection
    :return: connection
    """
    return get_sqlalchemy_engine().connect()


def execute_query(query):
    """
    Executes a mysql query
    :param str query: Sql query to be executed
    :return: cursor
    """
    connection = get_db_connection()
    result = connection.execute(query)
    connection.close()
    return result


def make_a_post_call_to_the_facebook(data):
    """
    Makes a post call to the facebook with data
    :param dict data: dict which contains params e.g: user_id, action or message
    """
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + ACCESS_TOKEN, json=data)
    print resp.content


def sender_action(user_id, action):
    """
    Lets Facebook know what bot's doing e.g: typing_on or typing_off
    :param str user_id: Facebook user Id
    :param str action: Bot's action
    """
    data = {
        "recipient": {"id": user_id},
        "sender_action": action
    }
    make_a_post_call_to_the_facebook(data)


def reply_on_facebook(user_id, msg):
    """
    Replies to facebook user
    :param str user_id: facebook user id who has sent us message
    :param str msg: Our response message
    """
    data = {
        "recipient": {"id": user_id},
        "message": {"text": msg}
    }
    make_a_post_call_to_the_facebook(data)


def send_mail_via_api(recipient, subject, message):
    """
    Sends Email to the recipient via mailgun API
    :param str recipient: Email sender
    :param str subject: Subject of email
    :param str message: Email response message
    :return: response
    """
    return requests.post(
        MAILGUN_SENDING_ENDPOINT,
        auth=("api", MAILGUN_API_KEY),
        data={"from": MAILGUN_FROM,
              "to": recipient,
              "subject": subject,
              "html": '<html><img src="'+BOT_IMAGE+'" style="width: 9%;'
                                                   'display: inline;"><h5 style="display: table-cell;'
                                                   'vertical-align: top;margin-left: 1%;">'
                      + message+'</h5></html>'})


def get_total_sms_segments(tokens):
    """
    Breaks list of string lines into message segments and appends
    these segments in a dict with segment numbers as keys
    :param tokens: list of independent string lines
    :return: total number of message segments, dict of message segments
    :rtype: int, dict
    """
    split_response_message = ""
    dict_of_segments = {}
    segments = 0
    while len(tokens) > 0:
        try:
            while len(tokens[0]) + len(split_response_message) <= TEXT_MESSAGE_MAX_LENGTH\
                    and len(tokens) > 0:
                split_response_message = split_response_message + tokens.pop(0) + "\n"
            segments += 1
            dict_of_segments.update({segments: split_response_message})
            split_response_message = ""
        except IndexError:
            if len(split_response_message) > 0:
                segments += 1
                dict_of_segments.update({segments: split_response_message})
            return segments, dict_of_segments
    return segments, dict_of_segments
