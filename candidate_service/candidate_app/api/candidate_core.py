from graphql import (
    graphql,
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString
)

schema = GraphQLSchema(
    query=GraphQLObjectType(
        name='RootQueryType',
        fields={
            'hello': GraphQLField(
                type=GraphQLString,
                resolver=lambda *_: 'world'
            )
        }
    )
)

query = '{hello}'

result = graphql(schema, query)

print result.data

if __name__ == '__main__':
    print "start"
