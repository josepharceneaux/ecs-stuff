"""Tests for the Widget Service API"""
__author__ = 'erikfarmer'

import datetime
import json
import pytest

from widget_service.widget_app import app
from widget_service.common.models.misc import AreaOfInterest
from activity_service.common.models.misc import Culture
from activity_service.common.models.misc import Organization
from widget_service.widget_app import db
from widget_service.common.models.user import Domain

from widget_service.common.utils.handy_functions import randomword
from widget_service.common.utils.db_utils import get_or_create

APP = app.test_client()


@pytest.fixture(autouse=True)
def test_org(request):
    org_attrs = dict(name='Rocket League All Stars - {}'.format(randomword(8)))
    test_org, created = get_or_create(db.session, Organization, defaults=None, **org_attrs)
    if created:
        db.session.add(test_org)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_org)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_org


@pytest.fixture(autouse=True)
def test_culture(request):
    culture_attrs = dict(description='Foo {}'.format(randomword(12)), code=randomword(5))
    test_culture, created = get_or_create(db.session, Culture, defaults=None, **culture_attrs)
    if created:
        db.session.add(test_culture)
        db.session.commit()

    def fin():
        try:
            db.session.delete(test_culture)
            db.session.commit()
        except Exception:
            pass

    request.addfinalizer(fin)
    return test_culture


@pytest.fixture(autouse=True)
def create_test_domain(test_culture, test_org, request):
    test_domain = Domain(name=randomword(40), usage_limitation=0,
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime(2050, 4, 26),
                         organization_id=test_org.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=(randomword(100)),
                         default_culture_id=test_culture.id,
                         settings_json=randomword(55), updated_time=datetime.datetime.now())

    test_domain2 = Domain(name=randomword(40), usage_limitation=0,
                         expiration=datetime.datetime(2050, 4, 26),
                         added_time=datetime.datetime(2050, 4, 26),
                         organization_id=test_org.id, is_fair_check_on=False, is_active=1,
                         default_tracking_code=1, default_from_name=(randomword(100)),
                         default_culture_id=test_culture.id,
                         settings_json=randomword(55), updated_time=datetime.datetime.now())

    db.session.add(test_domain)
    db.session.add(test_domain2)
    db.session.commit()
    def fin():
        try:
            db.session.delete(test_domain)
            db.session.commit()
        except Exception:
            pass
    request.addfinalizer(fin)
    return test_domain


@pytest.fixture(autouse=True)
def create_test_AOIs(create_test_domain, request):
    aois = []
    for i in xrange(10):
        aois.append(
            AreaOfInterest(domain_id=create_test_domain.id, description=randomword(150),
                           parent_id=None)
        )
    for i in xrange(2):
            aois.append(
                AreaOfInterest(domain_id=create_test_domain.id + 1, description=randomword(150),
                               parent_id=None)
            )
    db.session.bulk_save_objects(aois)

    def fin():
        db.session.query(AreaOfInterest).filter(AreaOfInterest.domain_id == create_test_domain.id).delete()
        db.session.commit()
    request.addfinalizer(fin)
    return True


def test_api_returns_domain_filtered_aois(create_test_domain, request):
    response = APP.get('/widget/interests/{}'.format(create_test_domain.id))
    assert response.status_code == 200
    assert len(json.loads(response.data)['primary_interests']) == 10
