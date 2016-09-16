from graph_api_service.application import app
from graph_api_service.common.routes import GTApis
from flask_graphql import GraphQLView
from schema import schema


app.add_url_rule(
    rule='/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # for having the GraphiQL interface
    )
)

if __name__ == '__main__':
    app.run(port=GTApis.GRAPH_API_SERVICE_PORT, use_reloader=True, debug=False, threaded=True)
