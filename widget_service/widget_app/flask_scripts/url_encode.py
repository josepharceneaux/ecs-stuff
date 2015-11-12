__author__ = 'erikfarmer'

# Standard Library
from base64 import b64encode
from urllib import quote_plus
# Third Party
import simplecrypt
# Module Specific
from widget_service.common.models.user import Domain
from widget_service.common.models.widget import WidgetPage
from widget_service.common.utils.handy_functions import random_letter_digit_string
from widget_service.widget_app import db

simplecrypt.EXPANSION_COUNT = (10000, 10000, 10000)


def encode_domain_ids():
    raw_domains = db.session.query(Domain.id, Domain.name)
    domains = [{'encrypted_id': gt_url_encrypt(d.id), 'name': d.name} for d in raw_domains]
    for d in domains:
        print 'Domain: {} has an encrypted id of: {}'.format(d['name'], d['encrypted_id'])


def encode_widget_ids():
    raw_widgets = db.session.query(WidgetPage.id, WidgetPage.widget_name)
    widgets = [{'encrypted_id': gt_url_encrypt(w.id), 'template': w.widget_name} for w in raw_widgets]
    for w in widgets:
        print 'Widget: {} has an encrypted id of: {}'.format(w['template'], w['encrypted_id'])


def gt_url_encrypt(id):
    salt = random_letter_digit_string(64)
    formatted_id = '{}.{}'.format(id, salt)
    encrypted_id = simplecrypt.encrypt('heylookeveryonewegotasupersecretkeyoverhere', formatted_id)
    b64_id = b64encode(encrypted_id)
    url_formatted_id = quote_plus(b64_id)
    return url_formatted_id
