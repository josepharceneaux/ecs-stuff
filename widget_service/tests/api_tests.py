"""Tests for the Widget Service API"""
__author__ = 'erikfarmer'

import datetime
import pytest

from widget_service.common.models.misc import AreaOfInterest
from widget_service.common.models.db import db
from widget_service.common.models.user import Domain

from widget_service.common.utils.handy_functions import randomword


@pytest.fixture(autouse=True)
def create_test_domains(request):
    test_domain = Domain(name=randomword(40), usage_limitation=0,
                             expiration=datetime(2050, 4, 26), added_time=datetime(2050, 4, 26),
                             organization_id=1, is_fair_check_on=False, is_active=1,
                             default_tracking_code=1, default_from_name=(randomword(100)),
                             settings_json=randomword(55), updated_time=datetime.datetime.now())

    unsearched_domain = Domain(name=randomword(40), usage_limitation=0,
                             expiration=datetime(2050, 4, 26), added_time=datetime(2050, 4, 26),
                             organization_id=1, is_fair_check_on=False, is_active=1,
                             default_tracking_code=1, default_from_name=(randomword(100)),
                             settings_json=randomword(55), updated_time=datetime.datetime.now())

    db.session.bulk_save_objects([test_domain, unsearched_domain])

    return test_domain


@pytest.fixture(autouse=True)
def create_test_AOIs(create_test_domains, request):
    aois = []
    for i in xrange(10):
        aois.append(
            AreaOfInterest(domain_id=create_test_domains.id, description=randomword(150),
                           parent_id=None)
        )
    db.session.bulk_save_objects(aois)