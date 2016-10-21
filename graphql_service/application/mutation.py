import graphene
from graphql_service.candidate_application.modules.mutation import CandidateMutation


class Mutation(graphene.ObjectType):
    candidate_mutation = graphene.Field(CandidateMutation)