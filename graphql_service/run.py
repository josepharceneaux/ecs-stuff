"""
Initializer for graphql_service
"""
# Third Party
from graphene import Schema
from flask_graphql import GraphQLView

# Application Specific
from graphql_service.common.routes import GTApis
from graphql_service.application import app, logger
from graphql_service.common.talent_config_manager import TalentEnvs
from graphql_service.common.error_handling import InternalServerError

# Creating Schema
try:
    from graphql_service.application.query import Query
    from graphql_service.application.mutation import Mutation

    schema = Schema(query=Query, mutation=Mutation, auto_camelcase=False)
except Exception as e:
    logger.exception("Error: {}".format(e.message))
    raise InternalServerError('Unable to create schema because: {}'.format(e.message))

if __name__ == '__main__':
    # Adding URL Rule
    app.add_url_rule(
        rule='/graphql',
        view_func=GraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=app.config['GT_ENVIRONMENT'] == TalentEnvs.DEV  # graphiql should only run for testing
        )
    )

    app.run(host='0.0.0.0', port=GTApis.GRAPHQL_SERVICE_PORT, use_reloader=True, debug=False, threaded=True)
