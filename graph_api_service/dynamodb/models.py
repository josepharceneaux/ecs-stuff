"""
This file contains code that will create DynamoDB tables
Note: The AttributeType
"""
import boto3


def create_dynamo_tables():
    """
    Function will create the candidates table in DynamoDB
    Docs: http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html?dynamo#DynamoDB.Client.create_table
    """
    # Get the service resource
    dynamodb = boto3.resource('dynamodb')

    # Create table
    candidates_table = dynamodb.create_table(
        TableName='candidates',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'N'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table is exists
    candidates_table.meta.client.get_waiter('table_exists').wait(TableName='candidates')

    # Print out some data about the table
    print "table_item_count: {}".format(candidates_table.item_count)


if __name__ == '__main__':
    try:
        create_dynamo_tables()

    except Exception as e:
        print "\nUnable to create DynamoDB tables. Error: {}".format(e.message)
        pass
