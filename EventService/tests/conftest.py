import pytest
import datetime
import requests
from app.app import app as _app
from werkzeug.security import generate_password_hash, gen_salt
from gt_models.config import init_db, db_session
from gt_models.client import Client
from gt_models.token import Token
from gt_models.user import User
from gt_models.domain import Domain
from gt_models.culture import Culture
from gt_models.organization import Organization
from mixer._faker import faker
from mixer.backend.sqlalchemy import Mixer

init_db()

TESTDB = 'test_project.db'
TESTDB_PATH = "/tmp/{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH
APP_URL = 'http://127.0.0.1:5006/'

@pytest.fixture
def base_url():
    return APP_URL

@pytest.fixture(scope='session')
def app(request):
    """
    Create a Flask app, and override settings, for the whole test session.
    """

    _app.config.update(
        TESTING=True,
        # SQLALCHEMY_DATABASE_URI=TEST_DATABASE_URI,
    )

    return _app


@pytest.fixture(scope='session')
def client(app, request):
    """
    Get the test_client from the app, for the whole test session.
    """
    return app.test_client()

@pytest.fixture()
def culture():
    mixer = Mixer(session=db_session, commit=True)
    culture = Culture.get_by_code('en-us')
    if culture:
        return culture
    else:
        culture = mixer.blend('gt_models.culture.Culture', code='en-us')
    return culture

@pytest.fixture()
def domain(request, organization, culture):
    now_timestamp = datetime.datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    mixer = Mixer(session=db_session, commit=True)
    domain = mixer.blend(Domain, organization=organization, culture=culture,
                         name=faker.nickname(), addedTime=now_timestamp)
    return domain

@pytest.fixture()
def organization(request):
    mixer = Mixer(session=db_session, commit=True)
    organization = mixer.blend('gt_models.organization.Organization')

    return organization

@pytest.fixture()
def user(request, culture, domain):
    mixer = Mixer(session=db_session, commit=True)

    user = mixer.blend(User, domain=domain, culture=culture, firstName=faker.nickname(),
                       lastName=faker.nickname(), email=faker.email_address(),
                       password=generate_password_hash('A123456', method='pbkdf2:sha512'))

    return user

@pytest.fixture()
def client_credentials(request, user):
    client_id = gen_salt(40)
    client_secret = gen_salt(50)
    client = Client(client_id=client_id, client_secret=client_secret)
    Client.save(client)
    return client

@pytest.fixture
def auth_data(user, base_url, client_credentials):
    # TODO; make the URL constant, create client_id and client_secret on the fly
    auth_service_url = "http://127.0.0.1:5005/oauth2/token"

    data = dict(client_id=client_credentials.client_id,
                client_secret=client_credentials.client_secret, username=user.email,
                password='A123456', grant_type='password')
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(auth_service_url, data=data, headers=headers)
    assert response.status_code == 200
    assert response.json().has_key('access_token')
    assert response.json().has_key('refresh_token')
    return response.json()

def teardown_fixtures(user, client_credentials, domain, organization):
    tokens = Token.get_by_user_id(user.id)
    for token in tokens:
        Token.delete(token.id)
    Client.delete(client_credentials.client_id)
    User.delete(user.id)
    Domain.delete(domain.id)
    Organization.delete(organization.id)
