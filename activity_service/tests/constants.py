from datetime import datetime, timedelta

TODAY = datetime.today()
CANDIDATE_UPDATE_START = TODAY - timedelta(days=30)
SMARTLIST_DELETE_START = TODAY - timedelta(days=22)
EVENT_CREATE_START = TODAY - timedelta(days=14)
CAMPAIGN_EMAIL_OPEN_START = TODAY - timedelta(days=7)
