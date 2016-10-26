# Third Party
from graphene import Schema
from flask_graphql import GraphQLView

# Application Specific
from graphql_service.common.models.db import db
from graphql_service.common.talent_config_manager import TalentEnvs
from graphql_service.common.error_handling import InternalServerError
from graphql_service.common.utils.models_utils import init_talent_app
from graphql_service.common.talent_config_manager import TalentConfigKeys

app, logger = init_talent_app(__name__)

# Creating Schema
try:
    from graphql_service.application.query import Query
    from graphql_service.application.mutation import Mutation

    schema = Schema(query=Query, mutation=Mutation, auto_camelcase=False)
except Exception as e:
    logger.exception("Error: {}".format(e.message))
    raise InternalServerError('Unable to create schema because: {}'.format(e.message))

# Adding URL Rule
app.add_url_rule(
    rule='/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        # graphiql should only run for testing
        graphiql=app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]
    )
)

try:
    db.create_all()
    db.session.commit()
except Exception as e:
    logger.exception("Could not start graphql_service in {env} environment because: {error}".format(
        env=app.config[TalentConfigKeys.ENV_KEY], error=e.message
    ))
