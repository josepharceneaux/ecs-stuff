import requests, json
from candidate_service.common.routes import CandidatePoolApiUrl


def create_smartlist(data, access_token):
    access_token = access_token if "Bearer" in access_token else "Bearer %s" % access_token
    response = requests.post(
            url=CandidatePoolApiUrl.SMARTLISTS,
            data=json.dumps(data),
            headers={'Authorization': access_token, 'content-type': 'application/json'}
    )
    return response
