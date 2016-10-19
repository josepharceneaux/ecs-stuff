import graphene
from common_resolvers import *


class EditFields(graphene.AbstractType):
    old_value = graphene.String()
    new_value = graphene.String()
    user_id = graphene.Int()
    updated_datetime = graphene.String(resolver=resolve_updated_datetime)

    def resolve_old_value(self, args, context, info):
        return self.get('old_value')

    def resolve_new_value(self, args, context, info):
        return self.get('new_value')

    def resolve_user_id(self, args, context, info):
        return self.get('user_id')


class FirstNameType(graphene.ObjectType, EditFields):
    pass


class LastNameType(graphene.ObjectType, EditFields):
    pass


class MiddleNameType(graphene.ObjectType, EditFields):
    pass


class FormattedNameType(graphene.ObjectType, EditFields):
    pass


class ResumeUrlType(graphene.ObjectType, EditFields):
    pass


class ObjectiveType(graphene.ObjectType, EditFields):
    pass


class SummaryType(graphene.ObjectType, EditFields):
    pass


class TotalMonthsExperienceType(graphene.ObjectType, EditFields):
    pass


class CandidateStatusIdType(graphene.ObjectType, EditFields):
    pass


class SourceIdType(graphene.ObjectType, EditFields):
    pass


class CultureIdType(graphene.ObjectType, EditFields):
    pass


class EditType(graphene.ObjectType):
    first_name = graphene.Field(type=FirstNameType, resolver=resolve_first_name)
    last_name = graphene.Field(type=LastNameType, resolver=resolve_last_name)
    middle_name = graphene.Field(type=MiddleNameType, resolver=resolve_middle_name)
    formatted_name = graphene.Field(type=FormattedNameType, resolver=resolve_formatted_name)
    resume_url = graphene.Field(type=ResumeUrlType, resolver=resolve_resume_url)
    objective = graphene.Field(type=ObjectiveType, resolver=resolve_objective)
    summary = graphene.Field(type=SummaryType, resolver=resolve_summary)
    total_months_experience = graphene.Field(type=TotalMonthsExperienceType, resolver=resolve_total_months_experience)
    candidate_status_id = graphene.Field(type=CandidateStatusIdType, resolver=resolve_candidate_status_id)
    source_id = graphene.Field(type=SourceIdType, resolver=resolve_source_id)
    culture_id = graphene.Field(type=CultureIdType, resolver=resolve_culture_id)

    # TODO: candidate subfields: emails, addresses, phones, etc.