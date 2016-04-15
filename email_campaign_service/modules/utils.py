# Standard Imports
import json
import HTMLParser
from urllib import urlencode
from datetime import datetime
from urlparse import (parse_qs, urlsplit, urlunsplit)

# Third Party
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

# Service Specific
from email_campaign_service.email_campaign_app import (logger, celery_app)

# Common Utils
from email_campaign_service.common.models.user import User
from email_campaign_service.common.models.misc import UrlConversion
from email_campaign_service.common.models.email_campaign import EmailCampaignSend
from email_campaign_service.common.utils.validators import raise_if_not_instance_of
from email_campaign_service.common.campaign_services.campaign_base import CampaignBase
from email_campaign_service.common.campaign_services.campaign_utils import CampaignUtils
from email_campaign_service.common.models.email_campaign import EmailCampaignSendUrlConversion
from email_campaign_service.common.routes import (CandidateApiUrl, EmailCampaignUrl)
from email_campaign_service.common.campaign_services.validators import \
    raise_if_dict_values_are_not_int_or_long
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import get_candidates_of_smartlist

DEFAULT_FIRST_NAME_MERGETAG = "*|FIRSTNAME|*"
DEFAULT_LAST_NAME_MERGETAG = "*|LASTNAME|*"
DEFAULT_PREFERENCES_URL_MERGETAG = "*|PREFERENCES_URL|*"
TRACKING_PIXEL_URL = "https://s3-us-west-1.amazonaws.com/gettalent-static/pixel.png"
TRACKING_URL_TYPE = 0
TEXT_CLICK_URL_TYPE = 1
HTML_CLICK_URL_TYPE = 2


@celery_app.task(name='get_candidates_from_smartlist')
def get_candidates_from_smartlist(list_id, campaign, candidate_ids_only=False, user_id=None):
    """
    Calls inter services method and retrieves the candidates of a smart or dumb list.
    :param list_id: smartlist id.
    :param campaign: email campaign object
    :param candidate_ids_only: Whether or not to get only ids of candidates
    :return:
    """
    candidates = get_candidates_of_smartlist(list_id=list_id, candidate_ids_only=candidate_ids_only,
                                             access_token=None,  user_id=user_id)
    return candidates


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
    unsubscribe_url = CandidateApiUrl.CANDIDATE_PREFERENCE
    # unsubscribe_url = current.HOST_NAME + URL(scheme=False, host=False, a='web',
    #                                           c='candidate', f='prefs',
    #                                           args=[candidate_id],
    #                                           hmac_key=current.HMAC_KEY)

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
    signed_source_url = CampaignUtils.sign_redirect_url(EmailCampaignUrl.URL_REDIRECT % url_conversion.id,
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
