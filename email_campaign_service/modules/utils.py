"""
Here we have helper functions used in email-campaign-service
"""
# Standard Imports
import os
import json
import uuid
import email
import poplib
import urllib
import smtplib
import imaplib
import HTMLParser
from _socket import gaierror
from urllib import urlencode
from base64 import b64decode
from datetime import datetime
from abc import abstractmethod
from urlparse import (parse_qs, urlsplit, urlunsplit)

# Third Party
from dateutil import parser
from bs4 import BeautifulSoup
from simplecrypt import decrypt
from dateutil.relativedelta import relativedelta

# Service Specific
from email_campaign_service.common.models.candidate import Candidate
from email_campaign_service.email_campaign_app import (logger, celery_app, cache, app)

# Common Utils
from email_campaign_service.common.redis_cache import redis_store
from email_campaign_service.common.models.misc import UrlConversion
from email_campaign_service.common.routes import EmailCampaignApiUrl
from email_campaign_service.common.models.user import User, Serializer
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.models.email_campaign import (EmailCampaignSend,
                                                                 EmailClientCredentials)
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from email_campaign_service.common.utils.validators import (raise_if_not_instance_of,
                                                            raise_if_not_positive_int_or_long)
from email_campaign_service.common.models.email_campaign import EmailCampaignSendUrlConversion
from email_campaign_service.common.error_handling import (InternalServerError, InvalidUsage)
from email_campaign_service.common.campaign_services.validators import raise_if_dict_values_are_not_int_or_long
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import get_candidates_of_smartlist

SIX_MONTHS_EXPIRATION_TIME = 15768000
DEFAULT_FIRST_NAME_MERGETAG = "*|FIRSTNAME|*"
DEFAULT_LAST_NAME_MERGETAG = "*|LASTNAME|*"
DEFAULT_PREFERENCES_URL_MERGETAG = "*|PREFERENCES_URL|*"
TRACKING_PIXEL_URL = "https://s3-us-west-1.amazonaws.com/gettalent-static/pixel.png"
TRACKING_URL_TYPE = 0
TEXT_CLICK_URL_TYPE = 1
HTML_CLICK_URL_TYPE = 2
TASK_ALREADY_SCHEDULED = 6057


@celery_app.task(name='get_candidates_from_smartlist')
def get_candidates_from_smartlist(list_id, candidate_ids_only=False, user_id=None):
    """
    Calls inter services method and retrieves the candidates of a smart or dumb list.
    :param list_id: smartlist id.
    :param candidate_ids_only: Whether or not to get only ids of candidates
    :param user_id: Id of user.
    :type list_id: int | long
    :type candidate_ids_only: bool
    :type user_id: int | long | None
    :rtype: list
    """
    raise_if_not_positive_int_or_long(list_id)
    raise_if_not_instance_of(candidate_ids_only, bool)
    raise_if_not_positive_int_or_long(user_id)
    candidates = get_candidates_of_smartlist(list_id=list_id, candidate_ids_only=candidate_ids_only,
                                             access_token=None, user_id=user_id)
    return candidates


@cache.cached(timeout=86400, key_prefix="X-TALENT-SERVER-KEY")
def jwt_security_key():
    """
    This function will return secret_key_id against which a secret_key will be stored in redis
    :return:
    """
    secret_key_id = str(uuid.uuid4())[0:10]
    secret_key = os.urandom(24).encode('hex')
    redis_store.setex(secret_key_id, secret_key, SIX_MONTHS_EXPIRATION_TIME)
    return secret_key_id


def do_mergetag_replacements(texts, candidate=None):
    """
    If no candidate, name is "John Doe"
    Replace MergeTags with candidate's first name, last name
    Replace preferences url
    """
    first_name = "John"
    last_name = "Doe"
    if candidate:
        first_name = candidate.first_name if candidate.first_name else "John"
        last_name = candidate.last_name if candidate.last_name else "Doe"

    new_texts = []
    for text in texts:
        # Do first/last name replacements
        text = text.replace(DEFAULT_FIRST_NAME_MERGETAG, first_name) if text and (
            DEFAULT_FIRST_NAME_MERGETAG in text) else text
        text = text.replace(DEFAULT_LAST_NAME_MERGETAG, last_name) if text and (
            DEFAULT_LAST_NAME_MERGETAG in text) else text

        # Do 'Unsubscribe' link replacements
        if candidate and text and (DEFAULT_PREFERENCES_URL_MERGETAG in text):
            text = do_prefs_url_replacement(text, candidate.id)

        new_texts.append(text)

    return new_texts


def do_prefs_url_replacement(text, candidate_id):

    assert candidate_id

    if app.config[TalentConfigKeys.ENV_KEY] == 'prod':
        host_name = 'https://app.gettalent.com/'
    else:
        host_name = 'http://staging.gettalent.com/'

    secret_key_id = jwt_security_key()
    secret_key = redis_store.get(secret_key_id)
    s = Serializer(secret_key, expires_in=SIX_MONTHS_EXPIRATION_TIME)

    payload = {
        "candidate_id": candidate_id
    }

    unsubscribe_url = host_name + ('candidates/%s/preferences?%s' % (str(candidate_id), urllib.urlencode({
        'secret_key_id': secret_key_id,
        'token': s.dumps(payload)
    })))

    # In case the user accidentally wrote http://*|PREFERENCES_URL|* or https://*|PREFERENCES_URL|*
    text = text.replace("http://" + DEFAULT_PREFERENCES_URL_MERGETAG, unsubscribe_url)
    text = text.replace("https://" + DEFAULT_PREFERENCES_URL_MERGETAG, unsubscribe_url)

    # The normal case
    text = text.replace(DEFAULT_PREFERENCES_URL_MERGETAG, unsubscribe_url)
    return text


def set_query_parameters(url, param_dict):
    """
    Given a URL, set or replace a query parameter and return the modified URL.
    Taken & modified from:
    http://stackoverflow.com/questions/4293460/how-to-add-custom-parameters-to-an-url-query-string-with-python

    :param url:
    :param param_dict:
    :return:
    """
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)

    for param_name, param_value in param_dict.items():
        if not query_params.get(param_name):
            query_params[param_name] = []
        query_params[param_name].append(param_value)

    new_query_string = urlencode(query_params, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query_string, fragment))


def create_email_campaign_url_conversion(destination_url, email_campaign_send_id,
                                         type_, destination_url_custom_params=None):
    """
    Creates url_conversion in DB and returns source url
    """

    # Insert url_conversion
    if destination_url_custom_params:
        destination_url = set_query_parameters(destination_url, destination_url_custom_params)

    url_conversion = UrlConversion(destination_url=destination_url, source_url='')
    UrlConversion.save(url_conversion)

    # source_url = current.HOST_NAME + str(URL(a='web', c='default', f='url_redirect',
    # args=url_conversion_id, hmac_key=current.HMAC_KEY))
    logger.info('create_email_campaign_url_conversion: url_conversion_id:%s' % url_conversion.id)
    signed_source_url = CampaignUtils.sign_redirect_url(EmailCampaignApiUrl.URL_REDIRECT % url_conversion.id,
                                           datetime.utcnow() + relativedelta(years=+1))

    # In case of prod, do not save source URL
    if CampaignUtils.IS_DEV:
        # Update source url
        url_conversion.update(source_url=signed_source_url)
    # Insert email_campaign_send_url_conversion
    email_campaign_send_url_conversion = EmailCampaignSendUrlConversion(email_campaign_send_id=email_campaign_send_id,
                                                                        url_conversion_id=url_conversion.id, type=type_)
    EmailCampaignSendUrlConversion.save(email_campaign_send_url_conversion)
    return signed_source_url


def create_email_campaign_url_conversions(new_html, new_text, is_track_text_clicks,
                                          is_track_html_clicks, custom_url_params_json,
                                          is_email_open_tracking, custom_html,
                                          email_campaign_send_id):
    soup = None

    # HTML open tracking
    logger.info('create_email_campaign_url_conversions: email_campaign_send_id: %s'
                % email_campaign_send_id)
    if new_html and is_email_open_tracking:
        soup = BeautifulSoup(new_html, "lxml")
        num_conversions = convert_html_tag_attributes(
            soup,
            lambda url: create_email_campaign_url_conversion(url, email_campaign_send_id,
                                                             TRACKING_URL_TYPE),
            tag="img",
            attribute="src",
            convert_first_only=True
        )

        # If no images found, add a tracking pixel
        if not num_conversions:
            image_url = TRACKING_PIXEL_URL
            new_image_url = create_email_campaign_url_conversion(image_url,
                                                                 email_campaign_send_id,
                                                                 TRACKING_URL_TYPE)
            new_image_tag = soup.new_tag("img", src=new_image_url)
            soup.insert(0, new_image_tag)

    # HTML click tracking
    if new_html and is_track_html_clicks:
        soup = soup or BeautifulSoup(new_html)

        # Fetch the custom URL params dict, if any
        if custom_url_params_json:

            destination_url_custom_params = json.loads(custom_url_params_json)
        else:
            destination_url_custom_params = dict()

        # Convert all of soup's <a href=> attributes

        convert_html_tag_attributes(
            soup,
            lambda url: create_email_campaign_url_conversion(url,
                                                             email_campaign_send_id,
                                                             HTML_CLICK_URL_TYPE,
                                                             destination_url_custom_params),
            tag="a",
            attribute="href"
        )

    # Add custom HTML. Doesn't technically belong in this function, but since we have access to the BeautifulSoup object, let's do it here.
    if new_html and custom_html:
        soup = soup or BeautifulSoup(new_html)
        body_tag = soup.find(name="body") or soup.find(name="html")
        """
        :type: Tag | None
        """
        if body_tag:
            custom_html_soup = BeautifulSoup(custom_html)
            body_tag.insert(0, custom_html_soup)
        else:
            logger.error("Email campaign HTML did not have a body or html tag, "
                         "so couldn't insert custom_html! email_campaign_send_id=%s",
                         email_campaign_send_id)

    # Convert soup object into new HTML
    if new_html and soup:
        new_html = soup.prettify()
        new_html = HTMLParser.HTMLParser().unescape(new_html)

    return new_text, new_html


def convert_html_tag_attributes(soup, conversion_function, tag="a",
                                attribute="href", convert_first_only=False):
    """
    Takes in BeautifulSoup object and calls conversion_function on every given
    attribute of given tag.

    :return:    Number of conversions done. (BeautifulSoup object is modified.)
    """
    items = soup.findAll(tag)
    replacements = 0
    for item in items:
        if item[attribute]:
            item[attribute] = conversion_function(item[attribute])
            replacements += 1
            if convert_first_only:
                break
    return replacements


def get_valid_send_obj(requested_campaign_id, send_id, current_user, campaign_type):
    """
    This gets the send object from EmailCampaignSend database table. If no object is found
    corresponding to given campaign_id, it raises ResourceNotFound.
    If campaign_id associated with send_obj is not same as the requested campaign id,
    it raises forbidden error.
    :param requested_campaign_id: Id of requested campaign object
    :param send_id: Id of send object of a particular campaign
    :param current_user: logged-in user's object
    :param campaign_type: Type of campaign. e.g. email_campaign etc
    :type requested_campaign_id: int | long
    :type send_id: int | long
    :type current_user: User
    :type campaign_type: str
    :exception: ResourceNotFound
    :exception: ForbiddenError
    :return: campaign blast object
    :rtype: EmailCampaignSend
    """
    raise_if_dict_values_are_not_int_or_long(dict(campaign_id=requested_campaign_id,
                                                  send_id=send_id))
    raise_if_not_instance_of(current_user, User)
    raise_if_not_instance_of(campaign_type, basestring)
    # Validate that campaign belongs to user's domain
    CampaignBase.get_campaign_if_domain_is_valid(requested_campaign_id,
                                                 current_user, campaign_type)
    return EmailCampaignSend.get_valid_send_object(send_id, requested_campaign_id)


class EmailClientBase(object):
    """
    This is the base class for email-clients.
    """

    def __init__(self, host, port, email, password, domain_id=None):
        """
        This sets values of attributes host, port, email and password.
        :param string host: Hostname of server
        :param string port: Port number
        :param string email: Email address
        :param string password: Password
        """
        self.host = host
        self.port = str(port).strip() if port else ''
        self.email = email
        self.password = password
        self.client = None
        self.connection = None
        self.domain_id = domain_id

    @staticmethod
    def get_client(host):
        """
        This gets the required client for given host.
        :param string host: Hostname e.g. smtp.gmail.com
        """
        if 'smtp' in host:
            client = SMTP
        elif 'imap' in host:
            client = IMAP
        elif 'pop' in host:
            client = POP
        else:
            raise InvalidUsage('Unknown host provided')
        return client

    @staticmethod
    def is_outgoing(host):
        """
        This returns True/False that given host is "outgoing" or not.
        :type host: string
        :rtype: bool
        """
        return any([client_type in host for client_type in EmailClientCredentials.OUTGOING])

    def connect(self):
        """
        This connects with SMTP/IMAP/POP server and sets the value of attribute 'connection'.
        """
        try:
            self.connection = self.client(self.host, port=self.port) if self.port else self.client(self.host)
        except gaierror as error:
            logger.exception(error.message)
            raise InternalServerError('Error occurred while connecting with given server')

    @abstractmethod
    def authenticate(self, connection_quit=True):
        """
        This will authenticate with email-client using email and password. Child classes will implement this.
        """
        pass

    @abstractmethod
    def import_emails(self):
        """
        This will import emails of user's account to getTalent database table email-conversations.
        Child classes will implement this.
        """
        pass

    def get_candidate_ids_and_emails(self):
        """
        This returns Ids and Emails of candidates in a user's domain.
        """
        candidates = Candidate.get_all_in_user_domain(self.domain_id)
        return [(candidate.id, candidate.emails) for candidate in candidates]


class SMTP(EmailClientBase):
    def __init__(self, host, port, email, password, domain_id=None):
        """
        This sets values of attributes host, port, email and password.
        :param string host: Hostname of SMTP server
        :param string port: Port number
        :param string email: Email address
        :param string password: Password
        """
        super(SMTP, self).__init__(host, port, email, password, domain_id=domain_id)
        self.client = smtplib.SMTP

    def authenticate(self, connection_quit=True):
        """
        This first connects with SMTP server. It then tries to login to server.
        """
        self.connection.starttls()
        try:
            self.connection.login(self.email, self.password)
        except smtplib.SMTPAuthenticationError as error:
            logger.exception(error.smtp_error)
            raise InvalidUsage('Invalid credentials provided. Could not authenticate with smtp server')
        if connection_quit:
            self.connection.quit()

    def send_email(self, to_address, subject, body):
        """
        This connects and authenticate with SMTP server and sends email to given email-address
        :param string to_address: Recipient's email address
        :param string subject: Subject of email
        :param string body: Body of email
        """
        self.connect()
        self.authenticate(connection_quit=False)
        msg = "From: %s\r\nTo: %s\r\nSubject: %s\n%s\n" % (self.email, to_address, subject, body)
        self.connection.sendmail(self.email, [to_address], msg)
        logger.info('Email has been sent from:%s, to:%s via SMTP server.' % (self.email, to_address))
        self.connection.quit()

    def import_emails(self):
        """
        We will only pass here as this client is of type "Outgoing"
        """
        pass


class IMAP(EmailClientBase):
    def __init__(self, host, port, email, password, domain_id=None):
        """
        This sets values of attributes host, port, email and password.
        :param string host: Hostname of SMTP server
        :param string port: Port number
        :param string email: Email address
        :param string password: Password
        """
        super(IMAP, self).__init__(host, port, email, password,domain_id=domain_id)
        self.client = imaplib.IMAP4_SSL

    def authenticate(self, connection_quit=True):
        """
        This first connects with IMAP server. It then tries to login to server.
        """
        try:
            self.connection.login(self.email, self.password)
        except imaplib.IMAP4_SSL.error as error:
            logger.exception(error.message)
            raise InvalidUsage('Invalid credentials provided. Could not authenticate with imap server')

    def import_emails(self):
        """
        This will import emails of user's account to getTalent database table email-conversations.
        """
        self.connect()
        self.authenticate()
        candidate_ids_and_emails = self.get_candidate_ids_and_emails()
        search_criteria = '(FROM "no-reply@gettalent.com")'
        typ, data = self.connection.search(None, search_criteria)
        print "%s emails found" % len(data[0])
        for num in data[0].split():
            typ, data = self.connection.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            # email_message = email.message_from_string(raw_email)
            msg = email.message_from_string(raw_email)
            print msg.get_payload(decode=True)
            for header in ['subject', 'to', 'from', 'date']:
                print '%s: %s' % (header.title(), msg[header])
            datetime_obj = parser.parse(msg['date'])
            print datetime_obj
            # continue inside the same for loop as above
            raw_email_string = raw_email.decode('utf-8')
            # converts byte literal to string removing b''
            email_message = email.message_from_string(raw_email_string)
            # this will loop through all the available multiparts in mail
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":  # ignore attachments/html
                    body = part.get_payload(decode=True)
                    print 'Body: %s' % body
            print '----------------------'
            # print 'Message %s\n%s\n' % (num, raw_email)
        # if msg_ids:
        #     msg_ids = ','.join(msg_ids.split(' '))
        self.connection.close()
        self.connection.logout()


class POP(EmailClientBase):
    def __init__(self, host, port, email, password, domain_id=None):
        """
        This sets values of attributes host, port, email and password.
        :param string host: Hostname of SMTP server
        :param string port: Port number
        :param string email: Email address
        :param string password: Password
        """
        super(POP, self).__init__(host, port, email, password, domain_id=domain_id)
        self.client = poplib.POP3_SSL

    def authenticate(self, connection_quit=True):
        """
        This first connects with POP server. It then tries to login to server.
        """
        try:
            self.connection.user(self.email)
            self.connection.pass_(self.password)
        except poplib.error_proto as error:
            logger.exception(error.message)
            raise InvalidUsage('Invalid credentials provided. Could not authenticate with pop server')

    def import_emails(self):
        """
        This will import emails of user's account to getTalent database table email-conversations.
        """
        pass


def format_email_client_data(email_client_data):
    """
    It returns the formatted data with leading and trailing white spaces stripped. It also encrypts the
    password to save in database.
    :param dict email_client_data: Data comping from front-end
    :return: Dictionary of formatted data
    :rtype: dict
    """
    return {key: value.strip() for key, value in email_client_data.iteritems()}


def decrypt_password(password):
    """
    This decrypts the given password
    :param string password: Login password of user for email-client
    """
    return decrypt(app.config[TalentConfigKeys.ENCRYPTION_KEY], b64decode(password))


# @celery_app.task(name='import_email_conversations')
def import_email_conversations(email_client):
    """
    This imports emails for given email-client
    """
    client_class = EmailClientBase.get_client(email_client.host)
    client = client_class(email_client.host, email_client.port, email_client.email,
                          decrypt_password(email_client.password), email_client.user.domain_id)
    client.import_emails()
