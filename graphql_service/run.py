"""
Start graphql_service
"""
# Application Specific
from graphql_service.application import app
from graphql_service.common.routes import GTApis

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=GTApis.GRAPHQL_SERVICE_PORT, use_reloader=True, debug=False, threaded=True)
