from flask_graphql import GraphQLView

from graphql_service.application import app
from graphql_service.common.routes import GTApis
from graphql_service.common.talent_config_manager import TalentEnvs
from graphql_service.modules.schema import schema

app.add_url_rule(
    rule='/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=app.config['GT_ENVIRONMENT'] == TalentEnvs.DEV  # graphiql should only run for testing
    )
)

if __name__ == '__main__':
    app.run(port=GTApis.GRAPHQL_SERVICE_PORT, use_reloader=True, debug=False, threaded=True)
