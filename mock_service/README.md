**TODO: Update this wiki page after making mock endpoint generic**

#### Need of mock service:

In social network service, we send multiple requests to various third party APIs like Meetup, Eventbrite, facebook and twitter etc. These third party APIs define some rules which vary from vendor to vendor. Like Eventbrite allows 4166 number of requests per hour to their API. But Meetup API allows 30 requests per 10 seconds. These limitations are there to avoid spamming / attack on the services. Whenever these limits are exceeded the API Services respond by taking some action. For instance in the case of Meetup API, if the limit is exceeded the IP address calling the service is flagged along with raising an exception (HIT_RATE_LIMIT). Generally when the code is executing in production we rarely have requests to the APIs exceeding the limits. However when the social network service tests are running the limits are exceeded. So, to avoid this, an alternative solution can be a separate mock service which acts like a vendor API and generates similar fake data as of original vendor. Also, instead of sending requests to actual vendor API, social network service will send request to mock service. Through this way, frequent requests limit can be removed and we will have social network service tests with same coverage.


#### Mock service


Mock service is a separate service written to avoid third party API calls without declining code coverage. Currently it serves only one endpoint.


**File Structure**

```

├── Dockerfile
├── __init__.py
├── mock_service_app
│   ├── app.py
│   ├── __init__.py
│   └── v1_mock.py
├── modules
│   ├── __init__.py
│   ├── mock_utils.py
│   └── vendors
│       ├── __init__.py
│       └── meetup.py
├── newrelic.ini
├── README.md
├── run.py
└── talent-uwsgi.ini

```


Consider the scenario below.

**Sequence Diagram**

![](https://www.dropbox.com/s/sygbb29548jwdyf/Sequence%20Diagram%20Mock%281%29.png?dl=1)

**Flow Chart**

![](https://www.dropbox.com/s/8yyfb302ojhph8l/mock-service-gettalent.png?dl=1)

**Endpoint**:

`/v1/<string:url_type>/<string:social_network>/<path:path>`


And the above endpoint can be called as following.

#### Example:

**Response OK:**

```

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

```

JSON schema code behind:

```

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

```

**Response Unauthorized:**


```
response = request.get('http://localhost:8016/v1/api/meetup/self/groups', headers={'Authorization': 'Invalid_header'})
print response.json()


"""

{

    'status_code': 401,
    'response': {
        'Unauthorized: User is not authorized to perform this request.'
    }

}

"""
```

JSON schema code behined


```


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


**JSON schema**:

Since mock service is not an actual service and returns dummy data, we need a structured schema to map request and response. See the JSON structure below.


```
{
   <PATH> : {
        <REQUEST-METHOD: {
            <DEFAULT-STATUS-CODE>: { # 200 is default status code
                   # Response to send
                   'status_code': <RESPONSE-STATUS-CODE>,
                   'response': <JSON-DICT>
            }
        }
    }
```


```
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
```

Above JSON data represents that if a `GET` request is made to `/self/member` endpoint then return response dict with `200` status code. In short, JSON schema is the dummy data you want to return in response if a particular request with a path(`/self/member`) is made to mock service.

**Conditional Requests:**

To make the mock service act like a real third party API needs conditional checking on the request data being passed. Like if headers or payload is not authorized then return unauthorized or Invalid Usage response.


See the JSON schema structure below for conditional requests.


```
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

The key thing in the above JSON is `expected_headers` and `on_fail`. If `expected_headers` dict is present in JSON schema then conditional response will be like below

* If request header matches with expected header, then return default `200` response.
* If request header is not matched with expected header, then redirect to key pair `on_fail` event present in `expected_headers` which returns `401` response in above case.


Note: For payload validation, use `expected_payload` keyword.


#### Steps to add a vendor in mock service:


* Create a new file in mock_service/modules/vendors/`<vendor-name>`.py
* Create a method like below in newly created file in step#1
```
def <vendor-name>_vendor(url_type, event_id=None):
    if url_type.lower() == AUTH:
        return {
        # Add AUTH related JSON schema here.
    }

    elif url_type.lower() == API:
        return {
        # Add API related JSON schema here.
    }

    else:
        return {}
```
* Register the above method in v1_mock.py
`register_vendor(<vendor-name>, <vendor-name>_vendor)`
* Add the new vendor in social_network_service/modules/constants.py
`MOCK_VENDORS = [MEETUP, <vendor_name>]`

