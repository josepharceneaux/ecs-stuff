"""Run Social Network Service APP"""
from social_network_service.common.routes import GTApis
from social_network_service.social_network_app.app import app

if __name__ == '__main__':
    from social_network_service.social_network_app.restful.v1_importer import schedule_importer_job
    # Schedule RSVP and Event importer general job
    schedule_importer_job()
    app.run(host='0.0.0.0', port=GTApis.SOCIAL_NETWORK_SERVICE_PORT, debug=False, threaded=True)
