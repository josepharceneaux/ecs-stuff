import graphene

# Graphene schema
from graph_api_service.modules.schema import CandidateType

# Models
from graph_api_service.common.models.candidate import Candidate


class QueryType(graphene.ObjectType):
    name = 'Query'

    candidate = graphene.Field(
        type=CandidateType,
        id=graphene.String()
    )

    # Using SQLAlchemy
    def resolve_candidate(self, args, info):
        candidate_id = args.get('id')
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return "Candidate not found"
        return candidate

        # Using DynamoDB
        # def resolve_candidate_for_dynamo(self, args, info):
        #     candidate_id = args.get('id')
