"""
This file contains mutation definition for various CUD operations on graphql objects
"""
import graphene
from graphql_service.candidate_application.modules.mutation import (
    CreateCandidate, UpdateCandidate, DeleteCandidate
)


class Mutation(graphene.ObjectType):
    create_candidate = CreateCandidate.Field()
    update_candidate = UpdateCandidate.Field()
    delete_candidate = DeleteCandidate.Field()
