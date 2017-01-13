# Activity Creation Class.
import json
from datetime import datetime
from activity_constants import ACTIVTY_PARAMS

from app_common.common.models.misc import Activity
from app_common.common.models.user import User


class TalentActivityManager(object):

    def __init__(self, db, activity_model=Activity, logger=None):
        """
        Allows flask-app/service to set flask-sqlalchemy db and Activity Models.
        :param db:
        :param activity_model:
        :param logger:
        """
        self.db = db
        self.activity_model = activity_model
        self.logger = logger

    def create_activity(self, params):
        """
        Consumes a dictionary and records an activity in the database.
        The dictionary keys:values type are as follows:
            {
                'activity_params': dict
                'activity_type': str
                'activity_type_id': int,
                'source_id': int
                'source_table': str,
                'user_id': int,
            }

            activity_params
                Values needed for string formatting by the front end. For example a new candidate
                activity requires the formatted name of said candidate and the username of the
                creator. This dict is validated by requiring certain keys and raies a UserWarning
                if not all keys are present. This is to prevent showing 'null' strings on the front
                end. These values are located at activity_constants.ACTIVITY_PARAMS

            activity_type
                String referencing the activity type. This is a human readable version of
                activity_type_id

            activity_type_id
                These ids correspond to the Activity.MessageId class located at
                app_common/common/models/misc.py
                Used in aggregating like activities.

            source_id
                This id is used to differentiate similar activities and refer to the original event.

            source_table:
                The name of the table the for the activity action (candidates for candidate creation).

            user_id
                The user responsible for the action.
        """

        required_keys = ACTIVTY_PARAMS[params['activity_type']]
        for item in required_keys:
            if not params['activity_params'].get(item):
                if self.logger:
                    self.logger.error('ActivityCreationError::MissingParam::{}'.format(item))
                return {
                    'committed': False,
                    'error': 'Missing param {}'.format(item)
                }

        activity = self.activity_model(
            user_id=int(params.get('user_id')),
            type=params.get('activity_type_id'),
            source_table=params.get('source_table'),
            source_id=params.get('source_id'),
            params=json.dumps(params.get('activity_params')),
            added_time=datetime.utcnow()
        )

        try:
            self.db.session.add(activity)
            self.db.session.commit()
            return {
                'committed': True,
                'id': activity.id
            }
        except Exception as e:
            return {
                'committed': False,
                'error': e.message
            }
