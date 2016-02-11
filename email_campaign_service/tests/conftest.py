__author__ = 'basit'

from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.tests.conftest import *
from email_campaign_service.common.models.email_marketing import EmailCampaign
from email_campaign_service.common.utils.handy_functions import add_role_to_test_user
from email_campaign_service.modules.email_marketing import create_email_campaign_smartlists
from email_campaign_service.common.tests.fake_testing_data_generator import FakeCandidatesData
from email_campaign_service.common.utils.candidate_service_calls import create_candidates_from_candidate_api
from email_campaign_service.common.inter_service_calls.candidate_pool_service_calls import create_smartlist_from_api


@pytest.fixture()
def email_campaign_of_user_first(user_first):
    """
    This fixture creates an email campaign in database table 'email_campaign'
    :param user_first:
    :return:
    """
    email_campaign_name = fake.name()
    reply_to_name = fake.name()
    email_campaign_subject = fake.sentence()
    campaign_body_html = "<html><body>Email campaign test</body></html>"
    email_campaign = EmailCampaign(name=email_campaign_name,
                                   user_id=user_first.id,
                                   is_hidden=0,
                                   email_subject=email_campaign_subject,
                                   email_from=fake.safe_email(),
                                   email_reply_to=reply_to_name,
                                   email_body_html=campaign_body_html,
                                   email_body_text="Email campaign test"
                                   )
    db.session.add(email_campaign)
    db.session.commit()
    return email_campaign


@pytest.fixture()
def campaign_with_smartlist(email_campaign_of_user_first, assign_roles_to_user_first,
                            access_token_first,  talent_pool):
    """
    This assigns smartlist ids with given campaign
    :param email_campaign_of_user_first:
    :return:
    """
    # create candidate
    smartlist_id, candidate_ids = create_smartlist_with_candidate(access_token_first,
                                                                  talent_pool)

    create_email_campaign_smartlists(smartlist_ids=[smartlist_id],
                                     email_campaign_id=email_campaign_of_user_first.id)
    return email_campaign_of_user_first


@pytest.fixture()
def assign_roles_to_user_first(user_first):
    """
    This assign required roles to user_first
    :param user_first:
    :return:
    """
    add_role_to_test_user(user_first, [DomainRole.Roles.CAN_ADD_CANDIDATES,
                                       DomainRole.Roles.CAN_GET_CANDIDATES])


def create_smartlist_with_candidate(access_token, talent_pool):
    # create candidate
    data = FakeCandidatesData.create(talent_pool=talent_pool, count=1)
    candidate_ids = create_candidates_from_candidate_api(access_token, data,
                                                         return_candidate_ids_only=True)
    smartlist_data = {'name': fake.word(),
                      'candidate_ids': candidate_ids}
    smartlists = create_smartlist_from_api(data=smartlist_data, access_token=access_token)
    smartlist_id = smartlists['smartlist']['id']
    return smartlist_id, candidate_ids
