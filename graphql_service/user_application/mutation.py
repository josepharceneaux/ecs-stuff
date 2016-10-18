import graphene
from graphql_service.user_application.models import User


class UserInputType(graphene.InputObjectType):
    pass


class UserMutation(graphene.relay.ClientIDMutation):

    id = graphene.ID()

    class Input(UserInputType):
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        email = graphene.String(required=True)


    @classmethod
    def mutate_and_get_payload(cls, input, context, info):

