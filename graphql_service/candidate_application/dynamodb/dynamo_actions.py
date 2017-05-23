"""
This module contains Dynamodb class which is for CRUD operation for candidate dynamodb table.
"""
from graphql_service.application import app
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from graphql_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs


class TableSelector(object):
    """
    This descriptor is to determine dynamodb table for different environments.
    e.g. if table name is xyz then it will be
        staging-xyz for staging
        prod-xyz for production
        xyz for local
        But currently this is not implemented so table name is same.
    """

    def __init__(self, table_name):
        self.table_name = table_name

    def __get__(self, instance, owner):
        if app.config['GT_ENVIRONMENT'] == TalentEnvs.DEV:
            table = boto3.resource('dynamodb', endpoint_url='http://localhost:8000').Table(self.table_name)
        else:
            table = boto3.resource('dynamodb', region_name='us-east-1').Table(self.table_name)
        return table


class DynamoDB(object):
    """
    Object will connect with candidate's table in dynamoDB via boto3

    Functions in this class follows the guidelines from boto3's docs:
      http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html

    More details are covered here: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Operations.html

    Note: the method table.delete() has been intentionally left out to prevent deleting
          any tables accidentally. Should deleting a table be required, it must be done
          via the AWS-DynamoDB's console: https://console.aws.amazon.com/dynamodb/home?region=us-east-1
    """
    candidate_table = TableSelector('candidate')

    # assert candidate_table.table_status in {'ACTIVE', 'UPDATING'}

    @classmethod
    def add_candidate(cls, data):
        """
        Will insert new candidate record

        Note: data may include 5 Python data-types for our purposes: string, int, long, decimal, and boolean
        More information: http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.NamingRulesDataTypes.html#HowItWorks.DataTypes

        :param data: candidate's dict-data
        :type data: dict
        """
        return cls.candidate_table.put_item(Item=data)

    @classmethod
    def get_attributes(cls, candidate_id, get_all_attributes=True, attributes=None):
        """
        will retrieve candidate data from dynamoDB and replace all Decimal objects with ints & floats
        :type candidate_id: int | long
        :type get_all_attributes: bool
        :type attributes: list[str]
        """
        if attributes:
            assert isinstance(attributes, list), 'attributes must be a list of candidate attributes'
            get_all_attributes = False

        if get_all_attributes is True:
            response = cls.candidate_table.get_item(Key={'id': str(candidate_id)})
        else:
            response = cls.candidate_table.get_item(
                Key={'id': str(candidate_id)},
                AttributesToGet=attributes
            )

        candidate_data = response.get('Item')
        if candidate_data:
            return replace_decimal(response['Item'])

        return None

    @classmethod
    def delete_attributes(cls, candidate_id, attributes):
        """
        Removes field/attribute from candidate's records
        :type candidate_id: int | long
        :param attributes: fields/attributes of candidate that will be deleted; e.g. "first_name", "phones", etc.
        :type attributes: list[str]
        """
        cls.candidate_table.update_item(
            Key={'id': str(candidate_id)},
            UpdateExpression='REMOVE {}'.format(','.join(item for item in attributes))
        )

    @classmethod
    def delete_candidate(cls, candidate_id):
        """
        Will delete all of candidate's records from dynamoDB
        :type candidate_id: int | long
        """
        return cls.candidate_table.delete_item(Key={'id': str(candidate_id)})

    @classmethod
    def update_candidate(cls, candidate_id, candidate_data):
        """
        Will update an existing candidate's attributes.
        If an attribute is provided, it will replace the attribute's existing data
        :type candidate_id: int | long
        :type candidate_data: dict
        """
        # Expression used to define what will be updated
        update_expressions = "SET "

        # Values that will be substituted in update_expression
        expression_attribute_values = {}

        for k, v in candidate_data.items():
            update_expressions += "{}=:{},".format(k, k)
            expression_attribute_values[':{}'.format(k)] = v

        return cls.candidate_table.update_item(
            Key={'id': str(candidate_id)},
            UpdateExpression=update_expressions[:-1],  # Remove the last comma from update_expression
            ExpressionAttributeValues=expression_attribute_values
        )

    @classmethod
    def update_archive_value(cls, candidate_id, archive_value):
        """
        Will set candidate's archive value to 1 or 0
        :type candidate_id: int | long
        :type archive_value: int
        :param archive_value: can only be 0 (false) or 1 (true)
        """
        return cls.candidate_table.update_item(
            Key={'id': str(candidate_id)},
            UpdateExpression="SET is_archived=:archive_value",
            ExpressionAttributeValues={":archive_value": archive_value}
        )

    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Method will return candidates belonging to user
        :param user_id: candidate's user-ID
        :type user_id: int
        :rtype: dict

        Return object example:
        >>> {
        >>>     'Count': 3057,
        >>>      'Items': [
        >>>          {'id': '851895', 'user_id': 512},
        >>>          {'id': '851895', 'user_id': 512}
        >>>      ],
        >>>      'ResponseMetadata': {'HTTPStatusCode': 200, 'RequestId': 'KHfnb234'},
        >>>      'ScannedCount': 3057
        >>> }
        """
        response = cls.candidate_table.query(IndexName='idx_user_id',
                                             KeyConditionExpression=Key('user_id').eq(user_id))

        # Convert Decimal object to Integer
        for item in response['Items'] or []:
            item['user_id'] = int(item['user_id'])

        return response

    @classmethod
    def paginate(cls, user_id, offset=None, chunk_size=100, candidate_id=None, select=None):
        """
        This function returns an iterator to iterate over all candidates of a user in chunks.
        User can specify chunk size, default is 100.

        :Example:
            >>> paginator = DynamoDB.paginate(119, chunk_size=1000)
            >>> for candidates in paginator:
            >>>     for candidate in candidates:
            >>>         print(candidate['id'])

        paginator object has a property "offset" which will help you to get candidates after that offset.
            >>> offset = paginator.offset
            >>> another_paginator = DynamoDB.paginate(119, offset=offset, chunk_size=1000)

        Now this paginator will fetch all those candidates those are after that offset. offset is a dictionary
        containing primary index, secondary index and sort key. something like
        offset = {
            "id": 123456,
            "user_id": 119,
            "added_datetime": "2017-01-01T00:00:00.0000000"
        }
        :param int|long user_id: user id (owner user id of candidate)
        :param dict|None offset: offset
        :param int chunk_size: How many records to retrieve
        :param int|long candidate_id: candidate unique id
        :param str select: select fields
        """
        assert not select or select in ['SPECIFIC_ATTRIBUTES', 'COUNT', 'ALL_ATTRIBUTES', 'ALL_PROJECTED_ATTRIBUTES']
        conditions = dict(IndexName='idx_user_id',
                          ScanIndexForward=True,
                          KeyConditionExpression=Key('user_id').eq(user_id),
                          Limit=chunk_size)
        if candidate_id:
            conditions['FilterExpression'] = Attr('id').gt(candidate_id)
        if isinstance(offset, dict):
            conditions['ExclusiveStartKey'] = offset
        if select:
            conditions['Select'] = select
        count_only = select == 'COUNT'
        return Paginator(cls.candidate_table, conditions, offset=offset, count_only=count_only)


class Paginator(object):
    """Iterate over all records lazily."""

    def __init__(self, table, conditions, offset=None, count_only=False):
        """
        This paginator can be used with any boto3 dynamodb table object. It allows you to paginate over large number
        of records in dynamodb table. For usage, look at the "Dynamodb.paginate()" method.
        :param type(t) table: boto3 table object
        :param dict conditions: dictionary containing query conditions
        :param dict offset: offset value, a dictionary
        :param bool count_only: if you want to get only count of candidates with given conditions.
        """
        self.table = table
        self.conditions = conditions
        self.offset = offset
        self.count_only = count_only

    def __iter__(self):
        return self

    def next(self):
        """
        This function is invoked on each iteration in for loop which then returns next chunk of candidates specified
        by conditions object.
        :return: list of candidates.
        """
        if self.offset is False:
            raise StopIteration('No more items to retrieve.')
        if self.count_only:
            self.conditions['Select'] = 'COUNT'
        else:
            if self.conditions.get('Select') == 'COUNT':
                self.conditions.pop('Select')
        if isinstance(self.offset, dict):
            self.conditions['ExclusiveStartKey'] = self.offset
        response = self.table.query(**self.conditions)
        self.offset = replace_decimal(response.get('LastEvaluatedKey', False))
        return response['Count'] if self.count_only else response['Items']


def replace_decimal(obj):
    """
    Function will convert all decimal.Decimal objects into integers or floats
    :return: input with updated data type: Decimal => integer | float
    """
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_decimal(obj[i])
        return obj
    elif isinstance(obj, dict):
        for key in obj.keys():
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
        for i in range(len(obj)):
            obj[i] = set_empty_strings_to_null(obj[i])
        return obj
    elif isinstance(obj, dict):
        for key in obj.keys():
            obj[key] = set_empty_strings_to_null(obj[key])
        return obj
    elif obj == '':
        return None
    else:
        return obj


# TODO: unit-test
def get_item(item_id, attribute_name, existing_data):
    # Retrieve same object from DDB
    relative_data = existing_data[attribute_name]
    if isinstance(relative_data, list):
        for item in relative_data:
            for k, v in item.iteritems():
                if k == 'id' and int(v) == item_id:
                    return v
    elif isinstance(relative_data, dict):
        for k, v in relative_data.iteritems():
            if k == 'id' and int(v) == item_id:
                return v


# TODO: unit-test
def update_data(item_id, attribute, existing_data, new_data):
    relative_data = existing_data[attribute]
    if isinstance(relative_data, list):
        for item in relative_data:
            for k, v in item.items():
                if k == 'id' and int(v) == item_id:
                    item[k] = new_data
    elif isinstance(relative_data, dict):
        for k, v in relative_data.items():
            if k == 'id' and int(v) == item_id:
                relative_data[k] = new_data
    return relative_data
