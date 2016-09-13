# Mock Service

### TODO: Update this wiki page after making mock endpoint generic

Mock service is a separate service written to avoid third party API calls. Currently it serves only one endpoint.


Endpoint:

`/v1/<string:url_type>/<string:social_network>/<path:path>`


And can be called as following.

Example:

```

Response OK:

response = request.get('http://localhost:8016/v1/api/meetup/self/member')
print response.json()


"""

{

    'status_code': 200,
    'response': {
        'id': 20242123
    }

}


"""

JSON schema code behind:

{

    '/self/member': {

        'GET': {
            '200': {
                   'status_code': 200,
                   'response': {
                           'id': 20242123
                       }
            }
        }

    }

}


Response Unauthorized:

response = request.get('http://localhost:8016/v1/api/self/groups', headers={'Authorization': 'Invalid_header'})
print response.json()


"""

{

    'status_code': 401,
    'response': {
        'Unauthorized: User is not authorized to perform this request.'
    }

}

"""


{

    '/self/groups': {

        'GET': {
            'expected_headers': {
                'headers': {
                    'Authorization': 'Bearer xyz'
                },
                'on_fail': 401
            }

            '200': {
                   'status_code': 200,
                   'response': {
                           'groups': [....]
                       }
            },

            '401': {
                'status_code': 401,
                    'response': {
                        'Unauthorized: User is not authorized to perform this request.'
                    }
            }
        }

    }

}



```

