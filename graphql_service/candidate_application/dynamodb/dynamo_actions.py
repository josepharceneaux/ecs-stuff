from datetime import datetime
import boto3
from decimal import Decimal
from graphql_service.application import app
from graphql_service.common.talent_config_manager import TalentEnvs
from graphql_service.common.utils.datetime_utils import DatetimeUtils


class DynamoDB(object):
    """
    Object will connect with candidate's table in dynamoDB via boto3

    Functions in this class follows the guidelines from boto3's docs:
      http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html

    Note: the method table.delete() has been intentionally left out to prevent deleting
          any tables accidentally. Should deleting a table be required, it must be done
          via the AWS-DynamoDB's console: https://console.aws.amazon.com/dynamodb/home?region=us-east-1
    """
    # Connection to candidates' table
    if app.config['GT_ENVIRONMENT'] == TalentEnvs.DEV:
        connection = boto3.resource('dynamodb', endpoint_url='http://localhost:8000', region_name='us-west-2')
    else:
        connection = boto3.resource('dynamodb')

    candidate_table = connection.Table('candidate')

    @classmethod
    def add_candidate(cls, data):
        """
        Will insert new candidate record

        Note: data may include only 5 Python data-types: string, int, long, decimal, and boolean
        :param data: candidate's dict-data
        :type data: dict
        """
        return cls.candidate_table.put_item(Item=data)

    @classmethod
    def get_candidate(cls, candidate_id):
        """
        will retrieve candidate data from dynamoDB and replace all Decimal objects with ints & floats
        :type candidate_id: int | long
        """
        response = cls.candidate_table.get_item(Key={'id': candidate_id})
        candidate_data = response.get('Item')
        if candidate_data:
            return replace_decimal(response['Item'])
        return None

    @classmethod
    def update_candidate(cls, candidate_id, candidate_data):
        """
        Will update an existing candidate's attributes.
        If an attribute is provided, it will replace the attribute's existing data
        :type candidate_id: int | long
        """
        # Expression used to define what will be updated
        update_expression = """SET
            first_name = :f_name, middle_name = :m_name, last_name = :l_name,
            source_id = :source_id, status_id = :status_id,
            objective = :objective, summary = :summary,
            resume_url = :resume_url, updated_datetime = :updated_datetime,"""

        # Values that will be substituted in update_expression
        expression_attribute_values = {
            ":f_name": candidate_data.get('first_name'),
            ":m_name": candidate_data.get('middle_name'),
            ":l_name": candidate_data.get('last_name'),
            ":source_id": candidate_data.get('source_id'),
            ":status_id": candidate_data.get('status_id'),
            ":objective": candidate_data.get('objective'),
            ":summary": candidate_data.get('summary'),
            ":resume_url": candidate_data.get('resume_url'),
            ":updated_datetime": candidate_data.get('updated_datetime') or DatetimeUtils.to_utc_str(datetime.utcnow())
        }

        # ***** Update expression will only be updated if candidate's attributes have been provided
        addresses = candidate_data.get('addresses')
        if addresses is not None:
            update_expression += 'addresses = :addresses,'
            expression_attribute_values[':addresses'] = addresses

        areas_of_interest = candidate_data.get('areas_of_interest')
        if areas_of_interest is not None:
            update_expression += 'areas_of_interest = :aois,'
            expression_attribute_values[':aois'] = areas_of_interest

        custom_fields = candidate_data.get('custom_fields')
        if custom_fields is not None:
            update_expression += 'custom_fields = :custom_fields,'
            expression_attribute_values[':custom_fields'] = custom_fields

        educations = candidate_data.get('educations')
        if educations is not None:
            update_expression += 'educations = :educations,'
            expression_attribute_values[':educations'] = educations

        emails = candidate_data.get('emails')
        if emails is not None:
            update_expression += 'emails = :emails,'
            expression_attribute_values[':emails'] = emails

        experiences = candidate_data.get('experiences')
        if experiences is not None:
            update_expression += 'experiences = :experiences,'
            expression_attribute_values[':experiences'] = experiences

        military_services = candidate_data.get('military_services')
        if military_services is not None:
            update_expression += 'military_services = :military_services,'
            expression_attribute_values[':military_services'] = military_services

        notes = candidate_data.get('notes')
        if notes is not None:
            update_expression += 'notes = :notes,'
            expression_attribute_values[':notes'] = notes

        phones = candidate_data.get('phones')
        if phones is not None:
            update_expression += 'phones = :phones,'
            expression_attribute_values[':phones'] = phones

        photos = candidate_data.get('photos')
        if photos is not None:
            update_expression += 'photos = :photos,'
            expression_attribute_values[':photos'] = photos

        preferred_locations = candidate_data.get('preferred_locations')
        if preferred_locations is not None:
            update_expression += 'preferred_locations = :preferred_locations,'
            expression_attribute_values[':preferred_locatoons'] = preferred_locations

        references = candidate_data.get('references')
        if references is not None:
            update_expression += 'references = :references,'
            expression_attribute_values[':references'] = references

        skills = candidate_data.get('skills')
        if skills is not None:
            update_expression += 'skills = :skills,'
            expression_attribute_values[':skills'] = skills

        social_networks = candidate_data.get('social_networks')
        if social_networks is not None:
            update_expression += 'social_networks = :social_networks,'
            expression_attribute_values[':social_networks'] = social_networks

        tags = candidate_data.get('tags')
        if tags is not None:
            update_expression += 'tags = :tags,'
            expression_attribute_values[':tags'] = tags

        work_preferences = candidate_data.get('work_preferences')
        if work_preferences is not None:
            update_expression += 'work_preferences = :work_preferences,'
            expression_attribute_values[':work_preferences '] = work_preferences

        edits = candidate_data.get('edits')
        if edits is not None:
            update_expression += 'edits = :edits,'
            expression_attribute_values[':edits'] = edits

        return cls.candidate_table.update_item(
            Key={'id': candidate_id},
            UpdateExpression=update_expression[:-1],  # Remove the last comma from update_expression
            ExpressionAttributeValues=expression_attribute_values
        )

    @classmethod
    def delete_candidate(cls, candidate_id):
        """
        Will delete all of candidate's records from dynamoDB
        :type candidate_id: int | long
        """
        return cls.candidate_table.delete_item(Key={'id': candidate_id})

    @classmethod
    def delete_attribute(cls, candidate_id, attribute):
        """
        Removes field/attribute from candidate's records
        :type candidate_id: int | long
        :param attribute: name of the field/attribute to be deleted; e.g. "educations", "phones", etc.
        :type attribute: str
        """
        cls.candidate_table.update_item(
            Key={'id': candidate_id},
            UpdateExpression='REMOVE {}'.format(attribute)
        )


def replace_decimal(obj):
    """
    Function will convert all decimal.Decimal objects into integers or floats
    :return: input with updated data type: Decimal => integer | float
    """
    if isinstance(obj, list):
        for i in xrange(len(obj)):
            obj[i] = replace_decimal(obj[i])
        return obj
    elif isinstance(obj, dict):
        for key in obj.iterkeys():
            obj[key] = replace_decimal(obj[key])
        return obj
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


def set_empty_strings_to_null(obj):
    """
    Function will set all empty-string-values to None, because
    DynamoDB does not accept empty-string-values
    """
    if isinstance(obj, list):
        for i in xrange(len(obj)):
            obj[i] = set_empty_strings_to_null(obj[i])
        return obj
    elif isinstance(obj, dict):
        for key in obj.iterkeys():
            obj[key] = set_empty_strings_to_null(obj[key])
        return obj
    elif obj == '':
        return None
    else:
        return obj
