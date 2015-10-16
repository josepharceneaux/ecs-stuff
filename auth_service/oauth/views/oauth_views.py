__author__ = 'ufarooqi'

from auth_service.oauth import app
from auth_service.oauth import gt_oauth
from auth_service.oauth import logger
from flask import request, jsonify
from flask.ext.cors import CORS


# Enable CORS
CORS(app, resources={
    r'/(oauth2|roles|users)/*': {
        'origins': '*',
        'allow_headers': ['Content-Type', 'Authorization']
    }
})



gt_oauth.grantgetter(lambda *args, **kwargs: None)
gt_oauth.grantsetter(lambda *args, **kwargs: None)


@app.route('/oauth2/token', methods=['POST'])
@gt_oauth.token_handler
def access_token(*args, **kwargs):
    return None


@app.route('/oauth2/revoke', methods=['POST'])
@gt_oauth.revoke_handler
def revoke_token():
    pass


@app.route('/oauth2/authorize')
@gt_oauth.require_oauth()
def authorize():
    if hasattr(request.oauth, 'error_message'):
        error_message = request.oauth.error_message or ''
        if error_message:
            error_code = request.oauth.error_code or None
            return jsonify({'error': {'code': error_code, 'message': error_message}}), 404

    user = request.oauth.user
    logger.info('User %s has been authorized to access getTalent api', user.id)
    return jsonify(user_id=user.id)

