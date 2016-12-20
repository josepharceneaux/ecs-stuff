"""
Here we have helper functions used in email-campaign-service
"""
# Standard Imports
import os
import json
import uuid
import urllib
import itertools
import HTMLParser
from urllib import urlencode
from datetime import datetime
from base64 import b64decode
from urlparse import (parse_qs, urlsplit, urlunsplit)
from operator import itemgetter

# Third Party
from bs4 import BeautifulSoup
from contracts import contract
from simplecrypt import decrypt
from dateutil.relativedelta import relativedelta

# Service Specific
from email_campaign_service.email_campaign_app import (logger, celery_app, cache, app)

# Common Utils
from email_campaign_service.common.redis_cache import redis_store
from email_campaign_service.common.models.misc import UrlConversion
from email_campaign_service.common.error_handling import InvalidUsage
from email_campaign_service.common.models.user import User, Serializer
from email_campaign_service.common.error_handling import InternalServerError
from email_campaign_service.common.talent_config_manager import TalentConfigKeys
from email_campaign_service.common.models.candidate import CandidateEmail, EmailLabel, Candidate
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.routes import (EmailCampaignApiUrl, get_web_app_url)
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from email_campaign_service.common.utils.validators import (raise_if_not_instance_of,
                                                            raise_if_not_positive_int_or_long)
from email_campaign_service.common.models.email_campaign import (EmailCampaignSendUrlConversion, EmailCampaignSend)
from email_campaign_service.common.campaign_services.validators import raise_if_dict_values_are_not_int_or_long
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import get_candidates_of_smartlist

SIX_MONTHS_EXPIRATION_TIME = 15768000
DEFAULT_FIRST_NAME_MERGETAG = "*|FIRSTNAME|*"
DEFAULT_USER_NAME_MERGETAG = "*|USERNAME|*"
DEFAULT_LAST_NAME_MERGETAG = "*|LASTNAME|*"
DEFAULT_PREFERENCES_URL_MERGETAG = "*|PREFERENCES_URL|*"
TEST_PREFERENCE_URL = get_web_app_url() + "/account/subscription-preferences"
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
    logger.info("There are %s candidates in smartlist(id:%s)" % (len(candidates), list_id))
    return candidates


@cache.cached(timeout=86400, key_prefix="X-TALENT-SERVER-KEY")
def jwt_security_key():
    """
    This function will return secret_key_id against which a secret_key will be stored in redis
    """
    secret_key_id = str(uuid.uuid4())[0:10]
    secret_key = os.urandom(24).encode('hex')
    redis_store.setex(secret_key_id, secret_key, SIX_MONTHS_EXPIRATION_TIME)
    return secret_key_id


@contract
def do_mergetag_replacements(texts, current_user, requested_object=None, candidate_address=None):
    """
    Here we do the replacements of merge tags with required values. This serves for candidate and user.
    If no candidate or user is provided, name is set to "John Doe".
    It replaces MergeTags with candidate's or user's first name, last name.
    It also replaces preferences URL only for candidate.
    :param list[> 0](string) texts: List of e.g. subject, body_text and body_html
    :rtype: list[> 0](string)
    """
    if not isinstance(current_user, User):
        raise InvalidUsage('Invalid object passed for user')
    if requested_object and not isinstance(requested_object, (Candidate, User)):
        raise InvalidUsage('Invalid object passed')

    first_name = "John"
    last_name = "Doe"

    if requested_object:
        first_name = requested_object.first_name if requested_object.first_name else first_name
        last_name = requested_object.last_name if requested_object.last_name else last_name

    new_texts = []
    merge_tag_replacement_dict = {DEFAULT_FIRST_NAME_MERGETAG: first_name,
                                  DEFAULT_LAST_NAME_MERGETAG: last_name,
                                  DEFAULT_USER_NAME_MERGETAG: current_user.name}
    for text in texts:
        if text:
            for key, value in merge_tag_replacement_dict.iteritems():
                if key in text:
                    # Do first_name, last_name and username replacements
                    text = text.replace(key, value)
            # Do 'Unsubscribe' link replacements
            if isinstance(requested_object, Candidate) and DEFAULT_PREFERENCES_URL_MERGETAG in text:
                text = do_prefs_url_replacement(text, requested_object, candidate_address)
            elif isinstance(requested_object, User) and DEFAULT_PREFERENCES_URL_MERGETAG in text:
                text = text.replace(DEFAULT_PREFERENCES_URL_MERGETAG, TEST_PREFERENCE_URL)

        new_texts.append(text)

    return new_texts


def do_prefs_url_replacement(text, candidate, candidate_address):
    """
    Here we do the replacement of merge tag "*|PREFERENCES_URL|*". After replacement this will become the
    URL for the candidate to unsubscribe the email-campaign.
    :param string text: This maybe subject, body_html or body_text of email-campaign
    :param Candidate candidate: Object of candidate to which email-campaign is supposed to be sent
    :param basestring candidate_address: Address of Candidate to which email campaign is being sent
    :rtype: string
    """
    candidate_id = candidate.id

    if not (isinstance(text, basestring) and text):
        raise InvalidUsage('Text should be non-empty string')
    if not (isinstance(candidate_id, (int, long)) and candidate_id):
        raise InvalidUsage('candidate_id should be positive int"long')
    host_name = get_web_app_url()
    secret_key_id = jwt_security_key()
    secret_key = redis_store.get(secret_key_id)
    s = Serializer(secret_key, expires_in=SIX_MONTHS_EXPIRATION_TIME)

    payload = {
        "candidate_id": candidate_id
    }

    unsubscribe_url = host_name + ('/candidates/%s/preferences?%s' % (str(candidate_id), urllib.urlencode({
        'token': '%s.%s' % (s.dumps(payload), secret_key_id),
        'email': candidate_address or ''
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
                                                                        url_conversion_id=url_conversion.id,
                                                                        type=type_)
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
    # Add custom HTML. Doesn't technically belong in this function, but since we have access to the BeautifulSoup
    # object, let's do it here.
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
        if item.get(attribute):
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


def get_candidate_id_email_by_priority(email_info_tuple, email_labels):
    """
    Get the primary_label_id from email_labels tuple list, using that find primary email address in emails_obj.
    If found then simply return candidate_id and primary email_address otherwise return first email address.
    :param (int, str, int) email_info_tuple: (candidate_id, email_address, email_label_id)
    :param [(int, str)] email_labels: Tuple containing structure [( email_label_id, email_label_description )]
    :return: candidate_id, email_address
    :rtype: tuple
    """
    if not(isinstance(email_info_tuple, list) and len(email_info_tuple) > 0):
        raise InternalServerError("get_candidate_id_email_by_priority: emails_obj is either not a list or is empty")

    # Get the primary_label_id from email_labels tuple list, using that find primary email address in emails_obj
    # python next method will return the first object from email_labels where primary label matches
    primary_email_id = int(next(email_label_id for email_label_id, email_label_desc in email_labels
                                if email_label_desc.lower() == EmailLabel.PRIMARY_DESCRIPTION.lower()))

    # Find primary email address using email label id
    candidate_email_tuple_iterator = ((candidate_id, email_address)
                                      for candidate_id, email_address, email_label_id in email_info_tuple
                                      if email_label_id == primary_email_id)

    candidate_id_and_email_address = next(candidate_email_tuple_iterator, None)

    # If candidate primary email is found, then just return that
    if candidate_id_and_email_address:
        return candidate_id_and_email_address

    # If primary email not found, then return first email which is last added email
    # Get first tuple from a list of emails_obj and return candidate_id and email_address
    candidate_id, email_address, _ = email_info_tuple[0]
    return candidate_id, email_address


def get_priority_emails(user, candidate_ids):
    """
    This returns tuple (candidate_id, email) choosing priority email form all the emails of candidate.
    :type user: User
    :type candidate_ids: list
    :rtype: list[tuple]
    """
    # Get candidate emails sorted by updated time and then by candidate_id
    candidate_email_rows = CandidateEmail.get_emails_by_updated_time_candidate_id_desc(candidate_ids)

    # list of tuples (candidate id, email address)
    group_id_and_email_and_labels = []

    # ids_and_email_and_labels will be [(1, 'saad_ryk@hotmail.com', 1), (2, 'saad_lhr@gmail.com', 3), ...]
    # id_email_label: (id, email, label)
    ids_and_email_and_labels = [(row.candidate_id, row.address, row.email_label_id)
                                for row in candidate_email_rows]

    # Again sorting on the basis of candidate_id
    ids_and_email_and_labels = sorted(ids_and_email_and_labels, key=itemgetter(0))
    """
    After running groupby clause, the data will look like
    group_id_and_email_and_labels = [[(candidate_id1, email_address1, email_label1),
        (candidate_id2, email_address2, email_label2)],... ]
    """

    for key, group_id_email_label in itertools.groupby(ids_and_email_and_labels,
                                                       lambda id_email_label: id_email_label[0]):
        group_id_and_email_and_labels.append(list(group_id_email_label))
    filtered_email_rows = []

    # Check if primary EmailLabel exist in db
    if not EmailLabel.get_primary_label_description() == EmailLabel.PRIMARY_DESCRIPTION:
        raise InternalServerError(
            "get_email_campaign_candidate_ids_and_emails: Email label with primary description not found in db.")

    # We don't know email_label id of primary email. So, get that from db
    email_label_id_desc_tuples = [(email_label.id, email_label.description)
                                  for email_label in EmailLabel.query.all()]

    # If there are multiple emails of a single candidate, then get the primary email if it exist, otherwise get any
    # other email
    for id_and_email_and_label in group_id_and_email_and_labels:
        _id, email = get_candidate_id_email_by_priority(id_and_email_and_label, email_label_id_desc_tuples)
        search_result = CandidateEmail.search_email_in_user_domain(User, user, email)
        if CandidateEmail.is_bounced_email(email):
            logger.info('Skipping this email because this email address is marked as bounced.'
                        'CandidateId : %s, Email: %s.' % (_id, email))
            continue
        # If there is only one candidate for an email-address in user's domain, we are good to go,
        # otherwise log error and send campaign email to that email id only once.
        if len(search_result) == 1:
            filtered_email_rows.append((_id, email))
        else:
            # Check if this email is already present in list of addresses to which campaign would be sent.
            # If so, omit the entry and continue.
            if any(email in emails for emails in filtered_email_rows):
                continue
            else:
                logger.error('%s candidates found for email address %s in user(id:%s)`s domain(id:%s). '
                             'Candidate ids are: %s'
                             % (len(search_result), email, user.id, user.domain_id,
                                [candidate_email.candidate_id for candidate_email in search_result]))
                filtered_email_rows.append((_id, email))
    
    return filtered_email_rows


@contract
def format_email_client_data(email_client_data):
    """
    It returns the formatted data with leading and trailing white spaces stripped. It also encrypts the
    password to save in database.
    :param dict email_client_data: Data comping from front-end
    :return: Dictionary of formatted data
    :rtype: dict
    """
    return dict(host=email_client_data.get('host').strip(),  # required
                port=email_client_data.get('port', '').strip(),
                email=email_client_data.get('email').strip(),  # required
                password=email_client_data.get('password').strip(),  # required
                name=email_client_data.get('name').strip(),  # required
                )


@contract
def decrypt_password(password):
    """
    This decrypts the given password
    :param string password: Login password of user for email-client
    """
    return decrypt(app.config[TalentConfigKeys.ENCRYPTION_KEY], b64decode(password))
