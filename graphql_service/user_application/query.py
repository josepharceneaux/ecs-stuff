import graphene
from graphene_sqlalchemy import SQLAlchemyConnectionField
from graphql_service.user_application.models import User


class UserQuery(graphene.ObjectType):
    users = SQLAlchemyConnectionField(User)
    user = graphene.Field(User, id=graphene.ID(required=True))

    def resolve_user(self, args, context, info):
        return User.get_node(id=int(args.get('id')), context=context, info=info)



