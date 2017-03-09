import boto3


def user_id_gsi():
    """
    Function will add user_id-global secondary index to existing candidate table
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
                'AttributeName': 'user_id',
                'AttributeType': 'N'
            }
        ],
        GlobalSecondaryIndexUpdates=[
            {
                'Create': {
                    'IndexName': 'idx_user_id',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'KEYS_ONLY'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1000,
                        'WriteCapacityUnits': 100
                    }
                }
            }
        ]
    )


if __name__ == '__main__':
    try:
        user_id_gsi()
    except Exception as e:
        print "Error: {}".format(e.message)
