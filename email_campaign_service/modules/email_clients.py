"""
    Author: Hafiz Muhammad Basit, QC-Technologies, <basit.gettalent@gmail.com>

    Here we have classes for email-clients.
    We have two types of email-clients.
        1) Outgoing (SMTP). This will serve in sending email-campaigns via user's personal email-account.
        2) Incoming (IMAP or POP). This will serve importing email-conversations from user's personal email-account.

    We have a base class EmailClientBase which has following methods.
        - connect()
        - authenticate()
        - import_emails()
        - get_candidate_ids_and_emails()
        - email_conversation_importer
        - save_email_conversations()
"""
# Standard Library
import email
import imaplib
import poplib
import smtplib
from _socket import gaierror
from abc import abstractmethod

# Third Party
from dateutil import parser
from contracts import contract

# Service Specific
from email_campaign_service.common.models.user import User
from email_campaign_service.common.models.candidate import Candidate
from email_campaign_service.email_campaign_app import logger, celery_app
from email_campaign_service.modules.utils import get_priority_emails, decrypt_password
from email_campaign_service.common.error_handling import (InvalidUsage, InternalServerError)
from email_campaign_service.common.models.email_campaign import (EmailClientCredentials, EmailConversations)


__author__ = 'basit'


class EmailClientBase(object):
    """
    - This is the base class for email-clients. This contains following methods:

    * __init__()
        - It takes "host", "port", "email", "password" and "user_id" as keyword argument and sets
            the values of respective attributes.

    * connect(self)
        This connects to client using "host" and "port".

    * authenticate()(self, connection_quit=True):
        This method is used to login into email-client's server using "email" and "password"

    * import_emails(self, candidate_id, candidate_email)
        This search selected mailbox for given candidate_email and saves email-conversation(s) by
        calling save_email_conversations().

    * get_candidate_ids_and_emails(self)
        This gets all the candidates in user's domain and gets their emails saved in our database table
        candidate_email.

    * email_conversation_importer(self)
        This selects mailbox (e.g. "INBOX") and imports email-conversations from the candidates of user.

    * save_email_conversations(self ,candidate_id, subject, body, email_received_datetime)
        This saves email-conversation in database table email-conversations. It also ensures
        saving unique records in database.
    """

    @contract
    def __init__(self, host, port, login_email, password, user_id=None, email_client_credentials_id=None):
        """
        This sets values of attributes host, port, email and password.
        :param string host: Hostname of server
        :param string port: Port number
        :param string login_email: Email address
        :param string password: Password
        :param int|long|None user_id: Id of user
        :param int|long|None email_client_credentials_id: Id of email_client_credentials object
        """
        self.host = host
        self.port = str(port).strip() if port else ''
        self.email = login_email
        self.password = password
        self.user_id = user_id
        self.email_client_credentials_id = email_client_credentials_id
        self.client = None
        self.connection = None
        self.mailbox = None

    @staticmethod
    @contract
    def get_client(host):
        """
        This gets the required client for given host.
        :param string host: Hostname e.g. smtp.gmail.com
        """
        host = host.strip().lower()
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
    @contract
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
        except smtplib.SMTPServerDisconnected as error:
            logger.exception(error.message)
            raise InternalServerError('Unexpectedly Connection closed with given server')

    @abstractmethod
    def authenticate(self, connection_quit=True):
        """
        This will authenticate with email-client using email and password. Child classes will implement this.
        """
        pass

    @abstractmethod
    def import_emails(self, candidate_id, candidate_email):
        """
        This will import emails of user's account to getTalent database table email-conversations.
        Child classes will implement this.
        """
        pass

    def get_candidate_ids_and_emails(self):
        """
        This returns Ids and Emails of candidates in a user's domain.
        """
        assert self.user_id, 'user_id is required for getting candidates'
        user = User.get_by_id(self.user_id)
        candidates = Candidate.get_all_in_user_domain(user.domain_id)
        candidate_ids = [candidate.id for candidate in candidates]
        return get_priority_emails(user, candidate_ids)

    def email_conversation_importer(self):
        """
        This imports email-conversations from the candidates of user.
        """
        candidate_ids_and_emails = self.get_candidate_ids_and_emails()
        self.connect()
        self.authenticate()
        return candidate_ids_and_emails

    @contract
    def save_email_conversation(self, candidate_id, subject, body, email_received_datetime):
        """
        This saves email-conversation in database table 'email_conversations'
        :param positive candidate_id: Id of candidate
        :param string subject: Subject of email
        :param string body: Body of email
        :param datetime email_received_datetime: Datetime object for the received datetime of email
        """
        assert self.user_id, 'user_id is required for saving email-conversations'
        assert self.email_client_credentials_id, \
            'email_client_credentials_id is required for saving email-conversations'
        email_conversation_in_db = EmailConversations.filter_by_keywords(user_id=self.user_id,
                                                                         candidate_id=candidate_id,
                                                                         subject=subject,
                                                                         body=body,
                                                                         email_client_credentials_id=
                                                                         self.email_client_credentials_id)
        if not email_conversation_in_db:
            email_conversation_data = {'user_id': self.user_id,
                                       'candidate_id': candidate_id,
                                       'mailbox': self.mailbox,
                                       'subject': subject,
                                       'body': body,
                                       'email_client_credentials_id': self.email_client_credentials_id,
                                       'email_received_datetime': email_received_datetime}
            email_conversation = EmailConversations(**email_conversation_data)
            EmailConversations.save(email_conversation)


class SMTP(EmailClientBase):
    """
    Class for connecting and sending emails with SMTP server
    """
    @contract
    def __init__(self, host, port, login_email, password, user_id=None, email_client_credentials_id=None):
        """
        This sets values of attributes host, port, email and password.
        :param string host: Hostname of SMTP server
        :param string port: Port number
        :param string login_email: Email address
        :param string password: Password
        :param int|long|None user_id: Id of user
        :param int|long|None email_client_credentials_id: Id of email_client_credentials object
        """
        super(SMTP, self).__init__(host, port, login_email, password, user_id=user_id,
                                   email_client_credentials_id=email_client_credentials_id)
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
            raise InvalidUsage('Invalid credentials provided. Could not authenticate with SMTP server')
        if connection_quit:
            self.connection.quit()

    @contract
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

    def import_emails(self, candidate_id, candidate_email):
        """
        We will only pass here as this client is of type "Outgoing"
        """
        pass


class IMAP(EmailClientBase):
    """
    Class for connecting and importing email-conversations with IMAP server
    """

    @contract
    def __init__(self, host, port, login_email, password, user_id=None, email_client_credentials_id=None):
        """
        This sets values of attributes host, port, email and password.
        :param string host: Hostname of SMTP server
        :param string port: Port number
        :param string login_email: Email address
        :param string password: Password
        :param int|long|None user_id: Id of user
        :param int|long|None email_client_credentials_id: Id of email_client_credentials object
        """
        super(IMAP, self).__init__(host, port, login_email, password, user_id=user_id,
                                   email_client_credentials_id=email_client_credentials_id)
        self.client = imaplib.IMAP4_SSL

    @contract
    def authenticate(self, connection_quit=True):
        """
        This first connects with IMAP server. It then tries to login to server.
        :type connection_quit: bool
        """
        try:
            self.connection.login(self.email, self.password)
        except imaplib.IMAP4_SSL.error as error:
            logger.exception(error.message)
            raise InvalidUsage('Invalid credentials provided. Could not authenticate with IMAP server')

    def email_conversation_importer(self):
        """
        This imports email-conversations from the candidates of user.
        """
        candidate_ids_and_emails = super(IMAP, self).email_conversation_importer()
        for mailbox in ("inbox",):
            self.mailbox = mailbox
            self.connection.select(mailbox)
            for candidate_id, candidate_email in candidate_ids_and_emails:
                self.import_emails(candidate_id, candidate_email)
            self.connection.close()
            self.connection.logout()

    @contract
    def import_emails(self, candidate_id, candidate_email):
        """
        This will import emails of user's account to getTalent database table email-conversations.
        :param positive candidate_id: Id of candidate
        :param string candidate_email: Email of candidate
        """
        search_criteria = '(FROM "%s")' % candidate_email
        typ, [searched_data] = self.connection.search(None, search_criteria)
        msg_ids = [msg_id for msg_id in searched_data.split()]
        logger.info("Account:%s, %s email(s) found from %s." % (self.email, len(msg_ids), candidate_email))
        for num in msg_ids:
            body = ''
            typ, data = self.connection.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            raw_email_string = raw_email.decode('utf-8')
            # converts byte literal to string removing b''
            email_message = email.message_from_string(raw_email_string)
            for header in ['subject', 'to', 'from', 'date']:
                logger.info('%s: %s' % (header.title(), email_message[header]))
            # convert string date to datetime object
            email_received_datetime = parser.parse(email_message['date'])
            # this will loop through all the available multiparts in mail
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":  # ignore attachments/html
                    body = part.get_payload(decode=True)
                    logger.info('Body: %s' % body)
            self.save_email_conversation(candidate_id, email_message['subject'].strip(),
                                         body.strip(), email_received_datetime)


class POP(EmailClientBase):
    """
    Class for connecting and importing email-conversations with POP server
    """

    def __init__(self, host, port, login_email, password, user_id=None, email_client_credentials_id=None):
        """
        This sets values of attributes host, port, email and password.
        :param string host: Hostname of POP server
        :param string port: Port number
        :param string login_email: Email address
        :param string password: Password
        :param int|long|None user_id: Id of user
        :param int|long|None email_client_credentials_id: Id of email_client_credentials object
        """
        super(POP, self).__init__(host, port, login_email, password, user_id=user_id,
                                  email_client_credentials_id=email_client_credentials_id)
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
            raise InvalidUsage('Invalid credentials provided. Could not authenticate with POP server')

    def email_conversation_importer(self):
        """
        This imports email-conversations from the candidates of user.
        """
        logger.info('POP email-conversations importer needs to be implemented')

    def import_emails(self, candidate_id, candidate_email):
        """
        This will import emails of user's account to getTalent database table email-conversations.
        """
        pass


@celery_app.task(name='import_email_conversations')
@contract
def import_email_conversations(queue_name):
    """
    This gets all the records for incoming clients from database table email_client_credentials.
    It then calls "import_email_conversations_per_account" to imports email-conversations for selected email-client.
    :type queue_name: string
    """
    email_client_credentials = \
        EmailClientCredentials.get_by_client_type(EmailClientCredentials.CLIENT_TYPES['incoming'])
    if not email_client_credentials:
        logger.info('No IMAP/POP email-client found in database')
    for email_client_credential in email_client_credentials:
        logger.info('Importing email-conversations from host:%s, account:%s, user_id:%s'
                    % (email_client_credential.host, email_client_credential.email, email_client_credential.user.id))
        import_email_conversations_per_client.apply_async([email_client_credential.host, email_client_credential.port,
                                                           email_client_credential.email,
                                                           email_client_credential.password,
                                                           email_client_credential.user.id,
                                                           email_client_credential.id], queue_name=queue_name)


@celery_app.task(name='import_email_conversations_per_client')
@contract
def import_email_conversations_per_client(host, port, login_email, password, user_id, email_client_credentials_id):
    """
    It imports email-conversations for given client credentials.
    :param string host: Host name
    :param string port: Port number
    :param string login_email: Email for login
    :param string password: Encrypted login password
    :param int|long user_id: Id of user
    :param int|long email_client_credentials_id: Id of email_client_credentials object
    """
    client_class = EmailClientBase.get_client(host)
    client = client_class(host, port, login_email, decrypt_password(password), user_id, email_client_credentials_id)
    client.email_conversation_importer()
