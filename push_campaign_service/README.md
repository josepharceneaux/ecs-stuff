# Push Campaign Service API


Push Campaign Service API allows users (recruiters) to send push notification campaigns to their
candidates. To send a push notification to a candidate, candidate must be registered with our app
using OneSignal API and we must have his device id (player_id in OneSignal terminology).

Users will be able to see the activities on the
campaign from activity history. In this API, we will implement functionality for
- Get all push campaigns created by a user/ recruiter
    + `/v1/push-campaigns [GET]`
- Create a push campaign
    + `/v1/push-campaigns [POST]`
- Get push campaign info using campaign id
    + `/v1/push-campaigns/:id [GET]`
- Update a push campaign
    + `/v1/push-campaigns/:id [PUT]`
- Delete a push campaign by id
    + `/v1/push-campaigns/:id [DELETE]`
- Schedule a push campaign
    + `/v1/push-campaigns/:id/schedule [POST]`
- Reschedule a push campaign
    + `/v1/push-campaigns/:id/schedule [PUT]`
- Unschedule a push campaign
    + `/v1/push-campaigns/:id/schedule [DELETE]`
- Send push campaign to candidates
    + `/v1/push-campaigns/:id/send [POST]`
- Get all "Sends" of a push campaign
    + `/v1/push-campaigns/:id/sends [GET]`
- Get all "Blasts" for a push campaign
    + `/v1/push-campaigns/:id/blasts [GET]`
- Get "Sends" of a specific blast of a push campaign
    + `/v1/push-campaigns/:id/blasts/:blast_id/sends [GET]`
- Get a specific "Blast" of a push campaign
    + `/v1/push-campaigns/:id/blasts/:blast_id [GET]`

### Devices
To send a push notification, this service makes use of OneSignal REST API for Push Notifications.
We specify the target candidate for a push notification using the `device_id (player_id for OneSignal)`. A device id is a unique
identifier for a device. Candidates have some registered `device_ids` and when this service
wants to send a campaign (push notification) to a candidate, it looks for associated device ids.
If candidate has no device registered with getTalent,
he will not get any push notifications and if device is associated with a candidate, we will send push notification to this device using
device_id.
A device will be associated to a candidate by sending a POST request to candidate service 
`Associate Devices Endpoint [/v1/candidates/:id/devices] with one signal device id as request payload.
OneSignal device id will be retrieved by OneSignal Javascript SDK for web (because we are dealing with web push notifications).

### Sends
Every campaign has `sends` which is the information about campaign i.e. to whom (candidate) this campaign was sent.
Sends are associated to a campaign through campaign blast, i.e. a campaign may have multiple
blasts and each blast has one or more sends. So for example, if we are supposed to send 50 messages
in a campaign to 50 candidates then the campaign must have 50 sends in the database
(after the messages have been sent).


### Blast
A campaign blast contains statistics of a campaign which includes number of sends and how many persons responded to a campaign `(clicks)`.
Every time a campaign is sent to smartlist/s, a new blast is created which may contain
different number of sends and clicks.

### Authentication
User access is based on access token. So you need to add `Authorization` header
with every request for authentication. Please read our docs at [AuthService] (http://docs.gettalentauth.apiary.io/#) to see
how to get access token.

All POST requests require `Authorization` header and `content-type` header if it you are sending data in request body.

+   Headers

        {'Authorization': 'Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE',
         'content-type': 'application/json'}

## How to:

### Create a Push Notification Campaign
To create a push notification campaign, You need to send a POST request to '/v1/push-campaigns' with JSON data like this
```
payload = {
    'name': 'getTalent',
    'body_text': 'Contents of a campaign goes here',
    'url': 'https://www.google.com',
    'smartlist_ids': [1,2,3]
}

```

### Schedule a Campaign
Firstly, you create a campaign draft (possibly in UI) but you need to schedule it to send it to
candidates associated with smartlists associated with this campaign.
To schedule a campaign, you need to send a POST request to '/v1/push-campaigns/{id}/schedule' endpoint with JSON data given below.
You need to also specify a frequency which can be any of the following:
- Frequencies:
    +  1 `(Once)`
    +  2 `(Daily)`
    +  3 `(Weekly)`
    +  4 `(Biweekly)`
    +  5 `(Monthly)`
    +  6 `(Yearly)`

```
payload =  {
                "frequency_id": 2,
                "start_datetime": "2015-11-26T08:00:00Z",
                "end_datetime": "2015-11-30T08:00:00Z"
           }
```


## Group Push Campaign

Resources related to Push Campaign.

## Push Campaigns [/v1/push-campaigns]

A PushCampaign object has the following attributes:
- PushNotification
    + `id (int):` unique id in table push_notification in getTalent database
    + `name (string):` normally name of website but can be anything
    + `body_text (string):` Body text of push campaign
    + `url (string):` A URL that will be opened when a user will click on a push notification
    + `frequency_id (int):` a unique id of frequency in getTalent database
    + `start_datetime (datetime string):` Date and time when campaign will start in ISO 8601 format
    + `end_datetime (datetime string):` Date and time when campaign will close in ISO 8601 format
    + `user_id (int):` Owner's id in getTalent database

### List All Campaigns [GET]

Returns a list of all push campaigns created by a specific user/recruiter.

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)

    + Body

            {
                "count": 2,
                "campaigns": [
                            {
                              "frequency_id": 1,
                              "id": 3,
                              "name": "New Campaign",
                              "start_datetime": "",
                              "body_text": "Notification body that will be shown to user in push notification popup",
                              "end_datetime": "",
                              "user_id": 1
                            },
                            {
                              "frequency_id": 1,
                              "id": 4,
                              "name": "Title Text",
                              "start_datetime": "",
                              "body_text": "Notification body that will be shown to user in push notification popup",
                              "end_datetime": "",
                              "user_id": 1
                            }
              ]
            }

+ Response 401 (application/json)

    + Body

            {
                "error":
                        {
                        "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 500 (application/json)


    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }



### Create a New Push Notification Campaign [POST]

User can create Push Notification campaign on this endpoint.
It takes a JSON object containing campaign data and returns campaign id from database
or returns an error message.

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE,
            content-type: application/json


    + Body

            {
                "name": "Campaign Title",
                "body_text": "Hi all, we have few openings at abc.com",
                "url": "https://www.google.com",
                "smartlist_ids": [1, 2, 3]

            }

+ Response 201 (application/json)

    + Headers

            Location: /v1/push-campaigns/3
    + Body

            {
                "id": 3,
                "message": "Push campaign was created successfully"
            }

+ Response 400 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent",
                            "additional_error_info": {
                                    "missing_fields":["body_text", "url"]
                            }
                        }
            }

+ Response 401 (application/json)


    + Body

            {
                "error":
                        {
                        "message": "Unauthorized to access getTalent"
                        }
            }


+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }

            {
                "error":
                        {
                            "code": 7003,
                            "message": "Some required fields are missing",
                            "missing_keys": ["name", "body_text"]
                        }
            }


### Delete Campaigns [DELETE]

Delete campaigns of a user by taking list of campaign ids.

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE,
            content-type: application/json
    + Body

            {
             "campaign_ids": [1, 2]
            }

+ Response 200 (application/json)

    + Body

            {
             "message": "Campaigns have been deleted from database"
            }

+ Response 207 (application/json)

    + Body

            {
             "message": "Not all campaigns deleted"
            }

+ Response 400 (application/json)

    + Body

            {
                "error":
                        {
                        "message": "Invalid usage"
                        }
            }

+ Response 401 (application/json)


    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Internal Server error occurred!"
                        }
            }


## Campaign by Id [/v1/push-campaigns/{id}]

+ Parameters
    + id (required) - ID of the push campaign in getTalent database


### Get Push Campaign Details [GET]

Returns detail of a single campaign based on campaign id.

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)

    + Body

            {
              "frequency_id": 1,
              "id": 3,
              "name": "New Campaign",
              "start_datetime": "",
              "body_text": "Notification body that will be shown to user in push notification popup",
              "end_datetime": "",
              "user_id": 1
            }
+ Response 401 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 403 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "User is not owner of this campaign"
                        }
            }

+ Response 404 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Push campaign not found"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }



### Update Campaign Details [PUT]

Update the contents of a push campaign.

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE,
            content-type: application/json
    + Body

            {
                "name": "Campaign Title",
                "body_text": "Hi all, we have few openings at abc.com",
                "url": "https://www.google.com",
                "smartlist_ids": [1, 2]

            }

+ Response 200 (application/json)


    + Body

            {
                "message": "Push campaign was updated successfully"
            }

+ Response 400 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent",
                            "additional_error_info": {
                                    "field":"body_text",
                                    "invalid_value": 0
                            }
                        }
            }


+ Response 401 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 403 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "User is not owner of this campaign"
                        }
            }

+ Response 404 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Push campaign not found"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }

### Delete Campaign [DELETE]

Deletes a campaign for given campaign id.

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)

    + Body

            {
                "message": "Campaign(id:%s) has been deleted successfully" % campaign_id
            }

+ Response 401 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 403 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Cannot delete Push campaign"
                        }
            }

+ Response 404 (application/json)

    + Body

            {
                "error":
                        {
                          "message": "Campaign not found"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }

## Schedule Campaign [/v1/push-campaigns/{id}/schedule]

### Schedule a Campaign [POST]

User can schedule a Push Notification campaign using this endpoint.
It takes a JSON object containing schedule data and returns
task_id(Task id on Scheduler Service) or returns an error message.

`start_datetime` and `end_datetime` must be in `2015-12-12T22:30:00Z` format and
for a periodic campaign, `start_datetime` must come before `end_datetime`

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE,
            content-type: application/json

    + Body

            {
                "frequency_id": 2,
                "start_datetime": "2015-11-26T08:00:00",
                "end_datetime": "2015-11-30T08:00:00"
            }

+ Response 200 (application/json)

    + Body

            {
                "task_id": "asbd3423bjdsab0907wfqwfih"
            }

+ Response 401 (application/json)


    + Body

            {
                "error":
                        {
                        "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 403 (application/json)


    + Body

            {
                "error":
                        {
                        "message": "Forbidden error"
                        }
            }

+ Response 404 (application/json)


    + Body

            {
                "error":
                        {
                        "message": "Campaign Not Found"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }


### Reschedule a Campaign [PUT]

User can reschedule a Push Notification campaign using this endpoint.
It takes a JSON object containing schedule data. It first removes existing task in
scheduler service for this campaign and creates a new task (either one-time or periodic) and then
returns task_id(Task id on Scheduler Service) or returns an error message.


`start_datetime` and `end_datetime` must be in `2015-12-12T22:30:00Z` format and
for a periodic campaign, `start_datetime` must come before `end_datetime`

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE,
            content-type: application/json

    + Body

            {
                "frequency_id": 2,
                "start_datetime": "2015-11-26T08:00:00",
                "end_datetime": "2015-11-30T08:00:00"
            }

+ Response 200 (application/json)

    + Body

            {
                "task_id": "asbd3423bjdsab0907wfqwfih"
            }

+ Response 401 (application/json)


    + Body

            {
                "error":
                        {
                        "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 403 (application/json)


    + Body

            {
                "error":
                        {
                        "message": "Forbidden error"
                        }
            }

+ Response 404 (application/json)


    + Body

            {
                "error":
                        {
                        "message": "Campaign Not Found"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }


## Send a campaign to smartlist/s [/v1/push-campaigns/{id}/send]

+ Parameters
    + id (required) - ID of the campaign which is to be sent

### Send a push notification campaign to candidates [POST]

This endpoint is used to send a Push Notification to candidates that are associated with
this campaign through smartlists. In our case, Scheduler Service will hit this endpoint to send a specific
campaign periodically as per the frequency of campaign.

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)

    + Body

            {
              "message": "Campaign was sent to 5 candidates"
            }

+ Response 401 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 404 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Push Notification campaign not found"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }

## Campaign Blasts by campaign Id [/v1/push-campaigns/{id}/blasts]

### Campaign Blasts [GET]

Every time a campaign is sent to some candidates, a campaign blast is created which contains
information about how many push notification were successfully sent and how many persons responded
to those sent push notifications.

This endpoint is used to get statistics of a campaign which includes multiple blasts where
each blast contains info about number of sends and how many responded to that campaign for that blast.

+ Parameters
    + id (required) - ID of the campaign in getTalent database

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)


    + Body

            {
                "count": 1,
                "blasts": [
                    {
                      "sends": 4,
                      "campaign_id": 468,
                      "updated_datetime": "2016-01-25 14:06:08",
                      "id": 631,
                      "clicks": 3
                    }
                ]
            }

+ Response 401 (application/json)


    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 404 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Campaign not found"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }


## Campaign Blast by campaign Id and Blast Id [/v1/push-campaigns/{campaign_id}/blasts/:id]

### Campaign Blast By Id [GET]

Every time a campaign is sent to some candidates, a campaign blast is created which contains
information about how many push notification were successfully sent and how many persons responded
to those sent push notifications.

This endpoint is used to get statistics of a campaign from blast object which contains info about number of sends and how many responded to that campaign for that specific send.


+ Parameters
    + id (required) - ID of the blast associated with campaign in getTalent database
    + campaign_id (required) - ID of the campaign in getTalent database

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)


    + Body

            {
                "blast": {
                    "sends": 4,
                    "campaign_id": 468,
                    "updated_datetime": "2016-01-25 14:06:08",
                    "id": 631,
                    "clicks": 3
                }
            }

+ Response 401 (application/json)


    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 404 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "push_campaign(id=467) not found."
                        }
            }

            {
                "error":
                        {
                            "message": "Blast not found for campaign (id: 468) with id 632"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }

## Campaign Sends by Id [/v1/push-campaigns/{id}/sends]

### Campaign Sends [GET]

This endpoint returns all sends of a campaign which may belong to different blast for
the same campaign. Every time a campaign is sent to candidates, a blast is created and
a campaign `send` to a candidate is associated with that blast.

+ Parameters
    + id (required) - ID of the campaign in getTalent database

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)


    + Body

            {
                "campaign_sends": [
                                {
                                  "candidate_id": 1,
                                  "id": 9,
                                  "sent_datetime": "2015-11-23 18:25:09"
                                },
                                {
                                  "candidate_id": 2,
                                  "id": 10,
                                  "sent_datetime": "2015-11-23 18:25:13"
                                }
                              ],
                "count": 2
            }

+ Response 401 (application/json)


    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 404 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Campaign not found"
                        }
            }

+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }

## Campaign Blast Sends by Id [/v1/push-campaigns/{id}/blasts/{blast_id}/sends]

### Campaign Blast Sends [GET]

This endpoint returns sends of a specific blast for a specific campaign since each blast may have
different number of sends. `sends` are associated to a campaign through a campaign blast.

+ Parameters
    + id (required) - ID of the campaign in getTalent database
    + blast_id (required) - ID of the blast that is associated with the campaign given by `id`

+ Request

    + Headers

            Authorization: Bearer edo9rdSKN8hYuc1zBWMfLXpXFd4ZbE

+ Response 200 (application/json)


    + Body

            {
                "blast_sends": [
                                {
                                  "candidate_id": 1,
                                  "id": 9,
                                  "sent_datetime": "2015-11-23 18:25:09"
                                },
                                {
                                  "candidate_id": 2,
                                  "id": 10,
                                  "sent_datetime": "2015-11-23 18:25:13"
                                }
                              ],
                "count": 2
            }

+ Response 401 (application/json)


    + Body

            {
                "error":
                        {
                            "message": "Unauthorized to access getTalent"
                        }
            }

+ Response 404 (application/json)

    + Body

            {
                "error":
                        {
                            "message": "Campaign not found"
                        }
            }

            {
                "error":
                        {
                            "message": "Blast does not belong to the specified campaign"
                        }
            }
+ Response 500 (application/json)

    + Body

            {
                "error": {
                    "message": "Internal Server error occurred!"
                }
            }
