from candidate_service.candidate_app import app
from social_network_service.common.utils.app_rest_urls import GTApis


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.CANDIDATE_SERVICE_PORT, use_reloader=True, debug=False)
