from common.tests.conftest import UserAuthentication
from common.tests.conftest import *

USER_PASSWORD = 'Talent15'


####################################
# test cases for oauth2 operations #
####################################
def test_user_authentication(sample_user, user_auth):
    """ Function tests getting, refreshing, and revoking auth token

    :type user_auth: UserAuthentication
    """
    user = sample_user

    # count of auth tokens currently in db
    current_number_of_tokens = Token.query.filter_by(user_id=user.id).count()

    # get auth token
    get_auth_token_resp = user_auth.get_auth_token(user_row=user, get_bearer_token=True)
    db.session.commit()
    print "\ntoken_row: %s" % get_auth_token_resp
    assert 'access_token' in get_auth_token_resp
    assert get_auth_token_resp['token_type'] == 'Bearer'
    assert 'refresh_token' in get_auth_token_resp
    assert Token.query.filter_by(user_id=user.id).count() == current_number_of_tokens + 1,\
        "a new token has been assigned to user"

    # refresh user's token
    resp = user_auth.refresh_token(user_row=user)
    db.session.commit()
    data = {'client_id': resp['token_row'].client_id,
            'refresh_token': resp['token_row'].refresh_token,
            'grant_type':'refresh_token'}
    r = requests.post('http://localhost:8001/oauth2/token', data=data)
    print "\ntoken_row for refreshing auth token: %s" % r.json()
    assert r.status_code == 200
    assert resp['token_row'].user_id == get_auth_token_resp['user_id']

    # revoke auth token
    user_auth.get_auth_credentials_to_revoke_token(user_row=user, auto_revoke=True)
    db.session.commit()
    assert Token.query.filter_by(user_id=user.id).count() == current_number_of_tokens, \
        "user's token has been removed"

###############################
# test cases for GETting user #
###############################
def test_get_user_without_authentication():
    """Function tests if user is authenticated before retrieving user data"""

    # Get user
    user_id = 5
    resp = requests.get('http://127.0.0.1:8004/v1/users/%s' % user_id)
    print "\nResponse to http://127.0.0.1:8004/v1/users/%s: \n%s" % (user_id, resp.content)

    assert resp.status_code == 401



