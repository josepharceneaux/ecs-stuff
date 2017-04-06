from activity_service.common.models.user import User
from activity_service.common.models.misc import Activity

def fetch_aggregated_activities(params):
    user_ids = User.query.filter_by(domain_id=params['domain_id']).values('id')
    flattened_user_ids = [item for sublist in user_ids for item in sublist]
    filters = [Activity.user_id.in_(flattened_user_ids)]
    start = params.start_param
    if start:
        filters.append(Activity.added_time >= start)
    activities = Activity.query.filter(*filters).order_by(Activity.added_time.desc()).limit(200).all()