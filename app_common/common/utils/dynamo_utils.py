"""
This contains functions to play with DynamoDB.
"""
import os

import boto3
from flask import current_app
from ..talent_config_manager import TalentConfigKeys, TalentEnvs
from ..campaign_services.campaign_utils import CampaignUtils

LOCAL_DYNAMO_URL = 'http://localhost:8000'


def _get_dynamo_connection(attribute='resource'):
    """
    This connects with DynamoDB depending upon environment.
    """
    boto_service = getattr(boto3, attribute)
    env = os.getenv(TalentConfigKeys.ENV_KEY) or TalentEnvs.DEV
    endpoint_url = LOCAL_DYNAMO_URL
    region_name = 'us-west-1'
    if env in [TalentEnvs.QA, TalentEnvs.PROD]:
        endpoint_url = 'https://dynamodb.us-east-1.amazonaws.com'  # TODO: Probably add in config file
        region_name = 'us-east-1'
    connection = boto_service('dynamodb', endpoint_url=endpoint_url, region_name=region_name)
    return connection


def create_dynamo_tables(table_name, primary_key=None):
    """
    Function will create the candidates table in DynamoDB
    Docs: http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html?dynamo#DynamoDB.Client.create_table
    """
    connection = _get_dynamo_connection(attribute='client')
    table_created = False

    if table_name not in connection.list_tables().get('TableNames'):
        primary_key = primary_key if primary_key else 'id'
        # Create table
        connection.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': primary_key,
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': primary_key,
                    'AttributeType': 'N'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Wait until the table exists
        connection.get_waiter('table_exists').wait(TableName=table_name)
        table_created = True

    logger = current_app.config[TalentConfigKeys.LOGGER]
    if table_created:
        logger.info("DynamoDB table:`{}` created.".format(table_name))
    else:
        logger.info("DynamoDB table:`{}` already exists.".format(table_name))


class DynamoDB(object):
    """
    Object will connect with candidate's table in dynamoDB via boto3

    Functions in this class follows the guidelines from boto3's docs:
      http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html

    Note: the method table.delete() has been intentionally left out to prevent deleting
          any tables accidentally. Should deleting a table be required, it must be done
          via the AWS-DynamoDB's console: https://console.aws.amazon.com/dynamodb/home?region=us-east-1

        For running Dynamo DB locally, kindly follow the instructions at
            http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html
    """
    connection = _get_dynamo_connection()


class EmailMarketing(DynamoDB):
    """
    Class for DynamoDB table 'email_marketing' to insert data in the table.
    """
    dynamo_table_name = 'email-marketing-stage' if CampaignUtils.IS_DEV else 'email_marketing'
    email_marketing_table = DynamoDB.connection.Table(dynamo_table_name)

    @classmethod
    def add_blast_id_and_candidate_ids(cls, data):
        """
        Note: data may include blast_id(Number) and candidate_ids(List)
        :param dict data: dict-data
        """
        return cls.email_marketing_table.put_item(Item=data)
