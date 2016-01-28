import json
import requests
from ..routes import CandidatePoolApiUrl


def create_smartlist_from_api(data, access_token):
    response = requests.post(
            url=CandidatePoolApiUrl.SMARTLISTS,
            data=json.dumps(data),
            headers={'Authorization': 'Bearer %s' % access_token,
                     'content-type': 'application/json'}
            )
    assert response.status_code == 201
    return response.json()
