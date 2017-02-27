import boto3


def owner_id_gsi():
    """
    Function will add owner_id-global secondary index to existing candidate table
    :return:
    """
    candidate_ddb = boto3.resource('dynamodb', region_name='us-east-1').Table('candidate')
    candidate_ddb.update(
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'owner_id',
                'AttributeType': 'N'
            }
        ],
        GlobalSecondaryIndexUpdates=[
            {
                'Create': {
                    'IndexName': 'idx_owner_id',
                    'KeySchema': [
                        {
                            'AttributeName': 'owner_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'KEYS_ONLY'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 100,
                        'WriteCapacityUnits': 10
                    }
                }
            }
        ]
    )


if __name__ == '__main__':
    try:
        owner_id_gsi()
    except Exception as e:
        print "Error: {}".format(e.message)
