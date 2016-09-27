"""
This file contains code that will create DynamoDB tables
Note: The AttributeType
"""
import boto3


def create_dynamo_tables(table_name, connect_to_local_db=True):
    """
    Function will create the candidates table in DynamoDB
    Docs: http://boto3.readthedocs.io/en/latest/reference/services/dynamodb.html?dynamo#DynamoDB.Client.create_table
    """
    # TODO: once testing is complete, we should dynamically set the appropriate dynamodb connection
    # Use local DynamoDB if connect_to_local_db is requested, otherwise connect to staging DynamoDB
    if connect_to_local_db:
        ddb = boto3.client('dynamodb', endpoint_url='http://localhost:8000', region_name='us-west-2')
    else:
        # Get the service resource
        ddb = boto3.client('dynamodb')

    if table_name not in ddb.list_tables().get('TableNames'):
        # Create table
        table = ddb.create_table(
            TableName=table_name,
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
        ddb.get_waiter('table_exists').wait(TableName=table_name)

        # Print out some data about the table
        print "table_item_count: {}".format(table.item_count)


if __name__ == '__main__':
    try:
        tables_to_create = ['candidates', 'users']
        map(create_dynamo_tables, tables_to_create)

    except Exception as e:
        print "\nUnable to create DynamoDB tables. Error: {}".format(e.message)
        exit(0)
