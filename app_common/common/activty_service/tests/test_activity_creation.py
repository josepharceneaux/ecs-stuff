from datetime import datetime

import pytest

from app_common.common.activty_service.activity_creator import TalentActivityManager
from app_common.common.models.db import db
from app_common.common.models.misc import Activity
from app_common.common.utils.models_utils import init_talent_app

app = init_talent_app('FakeAppForTesting')


def test_basic_create():
    tam = TalentActivityManager(db)
    params = {
        'activity_params': {},
        'activity_type': 'WIDGET_VISIT',
        'activity_type_id': 1,
        'added_time': datetime.utcnow(),
        'source_id': 1,
        'source_table': 1,
        'user_id': 1
    }
    output = tam.create_activity(params)
    assert output['committed'] is True

    # Clean up
    db.session.delete(Activity.get(output['id']))
    db.session.commit()


def test_basic_create_with_params():
    tam = TalentActivityManager(db)
    params = {
        'activity_params': {'username': 'Erik', 'formatted_name': 'Derek Framer'},
        'activity_type': 'CANDIDATE_CREATE_WEB',
        'activity_type_id': 1,
        'added_time': datetime.utcnow(),
        'source_id': 1,
        'source_table': 1,
        'user_id': 1
    }
    output = tam.create_activity(params)
    assert output['committed'] is True

    # Clean up
    db.session.delete(Activity.get(output['id']))
    db.session.commit()


def test_basic_create_missing_params():
    tam = TalentActivityManager(db)
    params = {
        'activity_params': {'username': 'Erik'},
        'activity_type': 'CANDIDATE_CREATE_WEB',
        'activity_type_id': 1,
        'added_time': datetime.utcnow(),
        'source_id': 1,
        'source_table': 1,
        'user_id': 1
    }

    with pytest.raises(UserWarning):
        output = tam.create_activity(params)
