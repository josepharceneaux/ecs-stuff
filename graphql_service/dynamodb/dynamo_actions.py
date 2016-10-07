import boto3
from decimal import Decimal
from graphql_service.application import app
from graphql_service.common.talent_config_manager import TalentEnvs


class DynamoDB(object):
    """
    Object will connect with candidate's table in dynamodb via boto3

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

    candidate_table = connection.Table('candidates')

    # Candidate attributes eligible for updating/adding
    candidate_attributes = {
        'addresses', 'emails', 'educations',
        'work_experiences', 'phones', 'skills',
        'military_services', 'social_networks'
    }

    @classmethod
    def get_candidate(cls, candidate_id):
        """
        will retrieve candidate data from dynamodb and replace all Decimal objects with ints & floats
        :type candidate_id: int | long
        """
        response = cls.candidate_table.get_item(Key={'id': candidate_id})
        candidate_data = response.get('Item')
        if candidate_data:
            return replace_decimal(response['Item'])
        return None

    @classmethod
    def delete_candidate(cls, candidate_id):
        """
        Will delete all of candidate's records from dynamodb
        :type candidate_id: int | long
        """
        return cls.candidate_table.delete_item(Key={'id': candidate_id})

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
    def add_item(cls, candidate_id, data):
        """
        Will add an item to candidate's records
        """
        # TODO: Add comment explaining the field check
        field = data.keys().pop()
        assert field in cls.candidate_attributes, "field: '{}' not recognized".format(field)

        for record in data[field]:
            cls.candidate_table.update_item(
                Key={'id': candidate_id},
                UpdateExpression='ADD {} = :value'.format(field),
                ExpressionAttributeValues={':value': record}
            )

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
