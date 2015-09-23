from SocialNetworkService.base import SocialNetworkBase
from SocialNetworkService.utilities import get_class, get_message_to_log, log_error
from gt_common.gt_models.social_network import SocialNetwork


def process_access_token(social_network_name, code_to_get_access_token, gt_user_id):
    message_to_log = get_message_to_log(function_name='process_access_token()',
                                        gt_user_id=gt_user_id)
    social_network = SocialNetwork.get_by_name(social_network_name)
    social_network_class = get_class(social_network_name, 'social_network')
    access_token, refresh_token = social_network_class.get_access_token(
        social_network,
        code_to_get_access_token)
    if access_token:
        user_credentials = dict(userId=gt_user_id,
                                socialNetworkId=social_network.id,
                                accessToken=access_token,
                                refreshToken=refresh_token,
                                memberId=None)
        # we have access token, lets save in db
        social_network_class.save_token_in_db(user_credentials)
    else:
        error_message = "Couldn't get access token for %s " % social_network_name
        message_to_log.update({'error': error_message})
        log_error(message_to_log)


# def event_importer():
#     member_id = get_member_id(social_network, access_token)
