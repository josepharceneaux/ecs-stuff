import graphene

from graph_api_service.common.models.db import db
from graph_api_service.common.models.user import Domain
from graph_api_service.common.models.candidate import Candidate, CandidateEmail
from schema import CandidateType, CandidateEmailType


class CachedData(object):
    CANDIDATE_ID = None


class CreateEmail(graphene.Mutation):
    email = graphene.Field('CandidateEmailType')

    class Input(object):
        address = graphene.String()
        label = graphene.String()  # TODO: maybe we can enforce only permissible inputs here?
        is_default = graphene.Boolean()

    @classmethod
    def mutate(cls, instance, args, info):

        label = (args.get('label') or '').title()

        for e_label, e_label_id in CandidateEmail.labels_mapping.iteritems():
            if label == e_label:
                email_label = e_label
                email_label_id = e_label_id
            else:
                email_label = 'Other'
                email_label_id = 4

        email_data = dict(
            candidate_id=CachedData.CANDIDATE_ID,
            email_label_id=email_label_id,
            address=args.get('address'),
            is_default=args.get('is_default')
        )

        # Save email data
        email = CandidateEmail(**email_data)
        db.session.add(email)
        db.session.commit()

        # Format inputs
        del email_data['email_label_id']
        del email_data['candidate_id']
        email_data.update(email_label=email_label, id=email.id)
        return CreateEmail(email=CandidateEmailType(**email_data))


class CreateCandidate(graphene.Mutation):
    ok = graphene.Boolean()
    id = graphene.Int()
    candidate = graphene.Field('CandidateType')

    class Input(object):
        """
        Class contains optional input fields for creating candidate
        """
        # Primary data
        first_name = graphene.String()
        middle_name = graphene.String()
        last_name = graphene.String()
        formatted_name = graphene.String()
        user_id = graphene.Int()
        filename = graphene.String()
        objective = graphene.String()
        summary = graphene.String()
        total_months_experience = graphene.Int()
        added_time = graphene.String()
        updated_datetime = graphene.String()
        candidate_status_id = graphene.Int()
        source_id = graphene.Int()
        culture_id = graphene.Int()

    @classmethod
    def mutate(cls, instance, args, info):
        candidate_data = dict(
            first_name=args.get('first_name'),
            middle_name=args.get('middle_name'),
            last_name=args.get('last_name'),
            formatted_name=args.get('formatted_name'),
            # user_id=request.user.id, # TODO: will work after user is authenticated
            filename=args.get('resume_url'),
            objective=args.get('objective'),
            summary=args.get('summary'),
            added_time=args.get('added_time'),
            candidate_status_id=args.get('status_id'),
            source_id=args.get('source_id'),
            culture_id=args.get('culuture_id')
        )

        # Save data using SQLAlchemy
        c = Candidate(**candidate_data)
        db.session.add(c)
        db.session.commit()
        CachedData.CANDIDATE_ID = c.id
        ok = True  # TODO: Dynamically set after adequate validations

        candidate_data.update(id=CachedData.CANDIDATE_ID)
        return CreateCandidate(candidate=CandidateType(**candidate_data), ok=ok)


class CandidateMutation(graphene.ObjectType):
    create_candidate = graphene.Field(CreateCandidate)
    create_email = graphene.Field(CreateEmail)
