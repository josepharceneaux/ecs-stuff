import graphene

# Models
from graph_api_service.common.models.candidate import Candidate
from graph_api_service.common.models.candidate import CandidateEmail
from graph_api_service.common.models.candidate import EmailLabel
from graph_api_service.common.models.user import Domain  # must be imported because Candidate is using it


class EmailLabelType(graphene.ObjectType):
    name = 'EmailLabel'

    labels_mapping = {1: 'Primary', 2: 'Home', 3: 'Work', 4: 'Other'}


class CandidateEmailType(graphene.ObjectType):
    name = 'CandidateEmail'

    id = graphene.Int()
    address = graphene.String()
    email_label = graphene.String()

    def resolve_email_label(self, args, info):
        for label_id, label in EmailLabelType.labels_mapping.iteritems():
            if self.email_label_id == label_id:
                return label


class CandidateAddressType(graphene.ObjectType):
    name = 'CandidateAddress'

    id = graphene.Int()
    address_line_1 = graphene.String()
    address_line_2 = graphene.String()
    city = graphene.String()
    state = graphene.String()
    zip_code = graphene.String()
    po_box = graphene.String()
    is_default = graphene.Boolean()
    coordinates = graphene.String()
    updated_time = graphene.String()  # Todo: update name to 'updated_datetime' & format timezones
    iso3166_subdivision = graphene.String()
    iso3166_country = graphene.String()


class CandidateType(graphene.ObjectType):
    """
    Note: Class variables must be identical to Candidate's class variables otherwise it
          will require a resolver
    """
    name = 'Candidate'

    # Primary attributes
    id = graphene.Int()
    first_name = graphene.String()
    middle_name = graphene.String()
    last_name = graphene.String()
    formatted_name = graphene.String()
    user_id = graphene.Int()
    resume_url = graphene.String()
    objective = graphene.String()
    summary = graphene.String()
    total_months_experience = graphene.Int()
    added_time = graphene.String()
    updated_datetime = graphene.String()
    candidate_status_id = graphene.Int()
    source_id = graphene.Int()
    culture_id = graphene.Int()

    # Secondary attributes & resolvers
    emails = graphene.List(CandidateEmailType)

    def resolve_emails(self, args, info):
        return self.emails  # using SQLAlchemy's associations


class QueryType(graphene.ObjectType):
    name = 'Query'

    candidate = graphene.Field(
        type=CandidateType,
        id=graphene.String()
    )

    def resolve_candidate(self, args, info):
        candidate_id = args.get('id')
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return "Candidate not found"
        return candidate


schema = graphene.Schema(query=QueryType)
