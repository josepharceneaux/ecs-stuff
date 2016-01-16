import json
import requests

from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit
from BeautifulSoup import BeautifulSoup, Tag
from email_campaign_service.email_campaign_app import logger
from email_campaign_service.common.models.db import db
from email_campaign_service.common.models.email_marketing import UrlConversion, EmailCampaignSendUrlConversion
from email_campaign_service.common.routes import CandidatePoolApiUrl, CandidateApiUrl

DEFAULT_FIRST_NAME_MERGETAG = "*|FIRSTNAME|*"
DEFAULT_LAST_NAME_MERGETAG = "*|LASTNAME|*"
DEFAULT_PREFERENCES_URL_MERGETAG = "*|PREFERENCES_URL|*"
TRACKING_PIXEL_URL = "https://s3-us-west-1.amazonaws.com/gettalent-static/pixel.png"
HTML_CLICK_URL_TYPE = 2
TRACKING_URL_TYPE = 0


def get_candidates_of_smartlist(oauth_token, list_id, candidate_ids_only=False):
    """
    Calls smartlist API and retrieves the candidates of a smart or dumb list.

    :param list_id: smartlist id.
    :return:
    """
    params = {'fields': 'candidate_ids_only'} if candidate_ids_only else {}
    r = requests.get(CandidatePoolApiUrl.SMARTLIST_CANDIDATES % list_id, params=params,
                     headers={'Authorization': oauth_token})
    response_body = json.loads(r.content)
    candidates = response_body['candidates']
    if candidate_ids_only:
        return [long(candidate['id']) for candidate in candidates]
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

    # source_url = current.HOST_NAME + str(URL(a='web', c='default', f='url_redirect', args=url_conversion_id, hmac_key=current.HMAC_KEY))
    source_url = 'http://localhost:8007/source_url'  # TODO
    url_conversion = UrlConversion(destination_url=destination_url, source_url=source_url)
    db.session.add(url_conversion)
    db.session.commit()
    # Insert email_campaign_send_url_conversion
    EmailCampaignSendUrlConversion(email_campaign_send_id=email_campaign_send_id, url_conversion_id=url_conversion.id,
                                   type=type_)
    return source_url


def create_email_campaign_url_conversions(new_html, new_text, is_track_text_clicks,
                                          is_track_html_clicks, custom_url_params_json,
                                          is_email_open_tracking, custom_html,
                                          email_campaign_send_id):
    soup = None

    # HTML open tracking
    if new_html and is_email_open_tracking:
        soup = BeautifulSoup(new_html)
        num_conversions = convert_html_tag_attributes(
            soup,
            lambda url: create_email_campaign_url_conversion(url, email_campaign_send_id, TRACKING_URL_TYPE),
            tag="img",
            attribute="src",
            convert_first_only=True
        )

        # If no images found, add a tracking pixel
        if not num_conversions:
            image_url = TRACKING_PIXEL_URL
            new_image_url = create_email_campaign_url_conversion(image_url, email_campaign_send_id, TRACKING_URL_TYPE)
            new_image_tag = Tag(soup, "img", [("src", new_image_url)])
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
