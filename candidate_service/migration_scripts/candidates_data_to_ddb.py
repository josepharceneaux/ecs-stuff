"""
Script will retrieve candidates' records and post them to DynamoDB
"""
from decimal import Decimal
import boto3

from candidate_service.candidate_app import app
from candidate_service.common.utils.iso_standards import get_country_code_from_name
from candidate_service.common.error_handling import NotFoundError
from candidate_service.common.models.candidate import Candidate
from candidate_service.common.models.user import User, Domain
from candidate_service.modules.notes import get_notes
from candidate_service.modules.tags import get_tags

ddb_candidate_table_connection = boto3.resource('dynamodb', region_name='us-east-1').Table('candidate')


def post_domain_candidates_to_gql_service(domain_id, number_of_candidates):
    domain_candidates = Candidate.query.join(User).join(Domain). \
        filter(Domain.id == domain_id).order_by(Candidate.added_time.desc()).limit(number_of_candidates).all()

    print "total number of candidates: {}".format(len(domain_candidates))

    unsuccessful = []
    successful = []

    for candidate in domain_candidates:
        candidate_id = candidate.id
        candidate = Candidate.query.get(candidate_id)
        try:

            # Candidate's records
            from candidate_service.modules.talent_candidates import fetch_candidate_info
            candidate_data = fetch_candidate_info(candidate)

            candidate_data['is_archived'] = candidate.is_archived

            # Candidate's notes
            candidate_notes = get_notes(candidate)['candidate_notes']
            if candidate_notes:
                candidate_data['notes'] = candidate_notes

            # Candidate's tags
            try:
                candidate_tags = get_tags(candidate_id)['tags']
                if candidate_tags:
                    candidate_data['tags'] = candidate_tags
            except NotFoundError:
                pass

            # Format candidate's data
            formatted_data = format_candidate_data_for_gql(candidate_data)
            ddb_candidate_table_connection.put_item(Item=formatted_data)
            successful.append(candidate_id)

        except Exception as e:
            unsuccessful.append(dict(candidate_id=candidate_id, error=e.message))
            continue

    return dict(successful=successful, unsuccessful=unsuccessful)


def format_candidate_data_for_gql(candidate_data):
    """
    Function will change candidate's data schema to conform with gQL's predefined schema for mutation
    :type candidate_data: dict
    :rtype candidate_data: dict
    """
    # Remove all white spaces and all empty data
    cleaned_candidate_data = dict()
    for k, v in candidate_data.items():
        if v != '' and v is not None:
            cleaned_candidate_data[k] = v.strip() if isinstance(v, basestring) else v

    # Format Required fields
    cleaned_candidate_data['talent_pool_id'] = cleaned_candidate_data['talent_pool_ids'][0]
    cleaned_candidate_data['added_time'] = cleaned_candidate_data['created_at_datetime']
    cleaned_candidate_data['source_product_id'] = cleaned_candidate_data['source_product_info']['id']

    # Remove duplicate fields
    remove_fields = ('talent_pool_ids', 'created_at_datetime', 'source_product_info')
    for field in remove_fields:
        del cleaned_candidate_data[field]

    # Format candidate's updated datetime
    updated_datetime = cleaned_candidate_data['updated_at_datetime']
    if cleaned_candidate_data.get('updated_at_datetime'):
        cleaned_candidate_data['updated_datetime'] = updated_datetime
        del cleaned_candidate_data['updated_at_datetime']

    # Work preference must be a list of dict
    if cleaned_candidate_data.get('work_preference'):
        cleaned_candidate_data['work_preferences'] = [cleaned_candidate_data['work_preference']]
        del cleaned_candidate_data['work_preference']

    # Remove all ID fields except candidate's ID
    cleaned_candidate_data = remove_ids(cleaned_candidate_data)
    cleaned_candidate_data['id'] = str(candidate_data['id'])

    # Set all boolean fields to False if not provided
    cleaned_candidate_data = set_booleans(cleaned_candidate_data)

    # Change country to iso3166-country codes
    cleaned_candidate_data = change_country_to_iso3166_country_code(cleaned_candidate_data)

    # Convert floats to Decimal
    cleaned_candidate_data = convert_float_to_decimal(cleaned_candidate_data)

    # Experiences' schema must match gQL's predefined schema
    # Ex. gQL schema has no notion of experience-bullets
    experiences = cleaned_candidate_data.get('work_experiences')
    if experiences:
        experiences = format_experiences(experiences)
        cleaned_candidate_data['experiences'] = experiences
        del cleaned_candidate_data['work_experiences']

    # Educations' schema must match gQL's predefined schema
    educations = cleaned_candidate_data.get('educations')
    if educations:
        educations = format_educations(educations)
        cleaned_candidate_data.update(educations=educations)

    return cleaned_candidate_data


def remove_ids(data):
    """
    Function will recursively remove all ID keys
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                remove_ids(v)
            if k == 'id':
                del data[k]
    if isinstance(data, list):
        for item in data:
            remove_ids(item)
    return data


def set_booleans(data):
    """
    :type data: dict
    Function will recursively set boolean-attribute's value to False if it has no value
    """
    for k, v in data.items():
        if isinstance(v, list):
            for item in v:
                set_booleans(item)
        if isinstance(v, dict):
            set_booleans(v)
        if k in ('is_current', 'is_default') and v is None:
            data[k] = False
    return data


def format_experiences(experiences):
    """
    Function will restructure experiences' schema to match gQL.
    :type experiences: list
    :rtype: list
    """
    for experience in experiences:

        # gQL experience schema will not accept the following keys
        experience.pop('subdivision', None)
        experience.pop('start_date', None)
        experience.pop('end_date', None)

        bullets = experience.get('bullets') or []
        for bullet in bullets:
            for k, v in bullet.items():
                if k == 'description':
                    experience[k] = v

        # gQL experience schema will not accept the experience-bullets
        experience.pop('bullets', None)

    return experiences


def format_educations(educations):
    """
    Function will restructure educations' schema to match gQL.
    :type educations: list
    :rtype: list
    """
    for education in educations:
        # gQL experience schema will not accept the following keys
        education.pop('subdivision', None)
        education.pop('added_time', None)

        degrees = education.get('degrees') or []
        for degree in degrees:
            # gQL experience schema will not accept the following keys
            degree.pop('type')
            degree.pop('start_date')
            degree.pop('end_date')

            bullets = degree.get('bullets') or []
            for bullet in bullets:
                degree['concentration'] = bullet.get('major')
                degree['comments'] = bullet.get('comments')

            degree.pop('bullets', None)

    return educations


def change_country_to_iso3166_country_code(dict_data):
    """
    Function will change 'country' key to 'iso3166_country' and its value to iso3166-country-code
    :param dict_data:
    :return:
    """
    for k, v in dict_data.items():
        if isinstance(v, list):
            for item in v:
                change_country_to_iso3166_country_code(item)
        elif isinstance(v, basestring):
            if k == 'country':
                if v and 'united states' in v.strip().lower():
                    dict_data['iso3166_country'] = 'US'
                dict_data['iso3166_country'] = get_country_code_from_name(v)
                del dict_data[k]
    return dict_data


def convert_float_to_decimal(obj):
    """
    Function will convert all decimal.Decimal objects into integers or floats
    :return: input with updated data type: Decimal => integer | float
    """
    if isinstance(obj, list):
        for i in xrange(len(obj)):
            obj[i] = convert_float_to_decimal(obj[i])
        return obj
    elif isinstance(obj, dict):
        for key in obj.iterkeys():
            obj[key] = convert_float_to_decimal(obj[key])
        return obj
    elif isinstance(obj, float):
        if obj % 1 == 0:
            return int(obj)
        else:
            return Decimal(obj)
    else:
        return obj


def test_dis():
    with app.app_context():
        r = post_domain_candidates_to_gql_service(domain_id=119, number_of_candidates=5000)
        print "r: {}".format(r)


# TODO: needs improvement and unit-tests
class GQL(object):
    def __init__(self, candidate_data, create=False):
        self.candidate_data = candidate_data
        self.create = create
        self.query_string = ""
        self.input = ""

        # Build mutation input for creating candidate via gQL
        if self.candidate_data:
            self.mutation_builder(self.candidate_data)

        if self.create is True:
            self.query_string += "mutation{create_candidate(input:{%s}){ok,id,error_code,error_message}}" % self.input

    def mutation_builder(self, candidate_data):
        for k, v in candidate_data.items():
            if isinstance(v, list) and v:
                self.input += '%s:[{' % k
                for i, item in enumerate(v, start=1):
                    if i > 1:
                        self.input += '{'
                    self.mutation_builder(item)
                    self.input += '},'
                    if i == len(v):
                        self.input += '],'
            elif isinstance(v, dict):
                self.input += '{'
                self.mutation_builder(v)
                self.input += '},'
            elif isinstance(v, bool):
                self.input += '%s: %s,' % (k, v)
            elif isinstance(v, basestring):
                self.input += '%s: "%s",' % (k, v)
            elif isinstance(v, (int, long)):
                self.input += '%s: %d,' % (k, v)
            elif isinstance(v, float):
                self.input += '%s: %.2f,' % (k, v)
        return self.input
