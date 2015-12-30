import json
import requests

from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit
from flask import current_app
from BeautifulSoup import BeautifulSoup, Tag
from email_campaign.common.common_config import CANDIDATE_SERVICE_BASE_URI
from email_campaign.common.models.db import db
from email_campaign.common.models.email_marketing import UrlConversion, EmailCampaignSendUrlConversion


DEFAULT_FIRST_NAME_MERGETAG = "*|FIRSTNAME|*"
DEFAULT_LAST_NAME_MERGETAG = "*|LASTNAME|*"
DEFAULT_PREFERENCES_URL_MERGETAG = "*|PREFERENCES_URL|*"
HTML_CLICK_URL_TYPE = 2
TRACKING_URL_TYPE = 0
# Candidate service URLs
SMARTLIST_CANDIDATES_URI = CANDIDATE_SERVICE_BASE_URI + '/v1/smartlist/get_candidates/'


def get_candidates(oauth_token, list_id, candidate_ids_only=False, count_only=False, max_candidates=0):
    """
    Gets the candidates of a smart or dumb list.

    :param max_candidates: If set to 0, will have no limit.
    :return:  dict of 'candidate_ids, total_found' if candidate_ids_only=True, otherwise returns
    what TalentSearch.search_candidates returns
    """
    return_fields = []
    if candidate_ids_only:
        return_fields.append('candidate_ids_only')
    if count_only:
        return_fields.append('count_only')
    if max_candidates:
        return_fields.append('max_candidates')
    query_params = {'id': list_id, 'return': ','.join(return_fields)}
    r = requests.get(SMARTLIST_CANDIDATES_URI, params=query_params,
                     headers={'Authorization': oauth_token})
    response_body = json.loads(r.content)
    candidates = response_body['candidates']
    if candidate_ids_only:
        # If candidate ids only are requested, get candidate ids and return
        return [candidate['id'] for candidate in candidates]
    return candidates


def do_mergetag_replacements(texts, candidate=None):
    """
    If no candidate, name is "John Doe"
    Replace MergeTags with candidate's first name, last name
    Replace preferences url with (....)?
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
    unsubscribe_url = 'http://localhost:8007/unsubscribe'
    # TODO: check for unsubscribe url
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
            # image_url = URL('static', 'images/pixel.png', host=True)
            image_url = "http://localhost:8014/static/images/pixel.png"  # TODO
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
            current_app.logger.error("Email campaign HTML did not have a body or html tag, "
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
