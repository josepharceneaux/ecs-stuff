"""Module for interacting with the Dice/BG API."""

import requests

from flask import current_app

from resume_parsing_app.views.app_constants import Constants as current


def parse_resume_with_bg(file_name, file_data):
    # Call Dice API with cached BurningGlass access token
    url = 'https://api.dice.com/profiles/resume/parse'
    try:
        payload = {'fileName': file_name, 'resumeData': file_data}
        burningglass_access_token = get_dice_login_dict().get('access_token')
        response = requests.post(url, json=payload, headers={'Authorization': 'Bearer %s' % burningglass_access_token})
    except requests.exceptions.RequestException:
        current_app.logger.error(
            "parse_resume: Received exception making request to {} to parse {}".format(url, file_name))
        return False

    # Return response or retry if access token expired
    if response.status_code == requests.codes.forbidden:
        current_app.logger.error(
            "parse_resume: Received forbidden response ({}) from Dice API ({}), so retrying".format(
                response.status_code, response.text))
        return parse_resume_with_bg(file_name, file_data)
    elif response.status_code == requests.codes.ok:
        return response.json()
    else:
        current_app.logger.error(
            "parse_resume_with_bg: Received error response from Dice. filename={}, response_code={}, response={}".format(
                file_name, response.status_code, response.text))
        return False


def get_dice_login_dict(username=current.BURNINGGLASS_USERNAME, password=current.BURNINGGLASS_PASSWORD):
    def call_request():
        return dice_resource_owner_credentials_oauth_login(username, password)

    # return current.cache.ram("burningglass_access_token", lambda: call_request(), time_expire=30000 if not force_cache else 0)
    return call_request()


def dice_resource_owner_credentials_oauth_login(username, password, dice_env='prod'):
    """
    Given a Dice username & password, returns a Dice user credentials dict, which has these keys:
    access_token, refresh_token, user_id, company_id.

    The full Dice user credentials dict looks like:
    {"access_token":"efda4283-1de6-4fac-a8ce-815a4441d9d6","token_type":"bearer","refresh_token":"535dc450-645b-49ae-834e-e1a191e3ec6a",
    "expires_in":43199,"scope":"access","client_id":"diceMobileApp","username":"osman.masood@dice.com","user_id":1681919,"user_type":"customer",
    "company_id":1,"permissions":{"dtnCommunications":false,"companyProfileAdmin":false,"companyNetworkAdmin":false,"recruiterNetworkProfile":false,
    "companyNetworkTMTab":false,"groupAccountAdmin":false,"groupAdd":false,"groupView":true,"groupUpdate":false,"groupDelete":false,"userView":true,
    "userUpdate":false,"userAddPrimaryGroupUsers":false,"userViewPrimaryGroupUsers":true,"userEditPrimaryGroupUsers":false,
    "userDeletePrimaryGroupUsers":false,"userAddAll":false,"userViewAll":true,"userEditAll":false,"userDeleteAll":false,"jobListingAdmin":false,
    "jobAdd":true,"jobView":true,"jobUpdate":true,"jobDelete":false,"siteAdmin":false,"siteSeekerManagement":false,"siteEmployerManagement":false,
    "siteMetroAreaManagement":false,"sitePartnerManagement":false,"siteAdManagement":false,"siteReports":false,"openWebSearch":true,
    "talentMatchSearch":true,"companyPermissions":{"integratedProfileView":true,"integratedSearch":true,"reports":true,"webJobEntry":true,
    "batchJobEntry":true,"webJobMaint":true,"accountMgmt":true,"emailEntireHotlist":true,"selfAdministered":true,"autologin":true,
    "displayContactEmail":true,"dtn":true,"fullNetwork":true,"showOFCCPName":true,"displayViews":true,"displayViewLimit":true,"easyApply":true,
    "boldAndHighlight":true,"profileExport":true,"canOptOutOfISearch":true,"webJobMaintenance":true,"diceGroup":true,"ofccp":true}}}

    :param username: Dice username
    :type username: basestring
    :param password: Dice password
    :type password: basestring
    :return: Dice user credentials dict
    :rtype: None | dict
    """

    # Get Dice domain
    dice_domain = _env_to_dice_domain(dice_env)

    url = "https://secure.%s.com/oauth/token" % dice_domain
    params = dict(grant_type="password", username=username, password=password)
    # TODO debug Logger
    try:
        response = requests.post(url,
                                 params=params,
                                 auth=(current.GETTALENT_CLIENT_ID, current.GETTALENT_CLIENT_SECRET))
        """ :type : requests.Response """
    except requests.exceptions.RequestException:
        # TODO log exception
        return None

    try:
        response_dict = response.json()
        access_token = response_dict.get(u'access_token')
        refresh_token = response_dict.get(u'refresh_token')
        if response_dict.get(u'error') == u'invalid_grant':
            # TODO bad credentials log
            return None
        elif not access_token or not refresh_token:
            # TODO logger error.
            return None
    except Exception as e:
        # TODO Log the exception or email admins
        return None
    return response_dict


def _env_to_dice_domain(dice_env):
    dice_domain = current.ENV_TO_DICE_DOMAIN.get(dice_env.lower())
    if not dice_domain:
        # TODO Log unknown Dice domain
        dice_domain = current.ENV_TO_DICE_DOMAIN.get('prod')
    return dice_domain
