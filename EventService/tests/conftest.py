import pytest
import datetime
import locale
from app import app as _app
from gt_models.config import init_db, db_session
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



@pytest.fixture(scope='session')
def app(request):
    """
    Create a Flask app, and override settings, for the whole test session.
    """

    _app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=TEST_DATABASE_URI,
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
    def domain_teardown():
        Domain.delete(domain.id)
    request.addfinalizer(domain_teardown)
    return domain

@pytest.fixture()
def organization(request):
    mixer = Mixer(session=db_session, commit=True)
    organization = mixer.blend('gt_models.organization.Organization')

    def organization_teardown():
        Organization.delete(organization.id)
    request.addfinalizer(organization_teardown)
    return organization

@pytest.fixture()
def user(request, culture, domain):
    mixer = Mixer(session=db_session, commit=True)

    user = mixer.blend(User, domain=domain, culture=culture, firstName=faker.nickname(),
                       lastName=faker.nickname(), email=faker.email_address())

    def user_teardown():
        User.delete(user.id)
    request.addfinalizer(user_teardown)
    return user


