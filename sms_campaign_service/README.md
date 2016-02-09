# SMS Campaign Service
Flask microservice for handling SMS campaigns

### Problem
We want recruiters to be able to send bulk SMSs to smartlists of candidates. We should be able to track the sends, 
responses and clicks. We should also be able to create smartlists for sending bulk SMSs.

Users can also set an SMS campaign to run periodically e.g. a User can set a campaign to 
run daily or monthly or even yearly.

### User
Recruiters/marketers need to send SMSs to candidates whom they want to market to. 
Currently, this is a manual process. 
For example: Let's say Kaiser is hosting a hiring event in New York. 
So Kaiser would want to contact all candidates in their talent pool who live around New York. 
getTalent would allow them to send targeted, personalized SMS campaigns (via a _smartlist_) to all 
these candidates. Such targeted campaigns usually result in a much higher response rate than the 
usual "spray and pray" spam messages. 

### High level overview
A front end will create a campaign, that can be run periodically. These campaigns have smartlists 
associated with them (smart lists have candidates in them). We are assuming, for now, that smartlists 
will be added through their own UI. So UI will do two things

* It will save the campaign in the database.
* It will schedule the campaign in the UI by hitting a _scheduler_service_ endpoint. 
For example, the UI might hit the _scheduler_service_ with some data 
(e.g. callback URL, frequency with which to hit the callback URL 
(e.g. daily, monthly or yearly) and etc) and then _scheduler_service_ will remember to hit the 
callback URL when it is time to execute the campaign.

### Directory structure

    ├── sms_campaign_service/
        ├── modules/
            ├── custom_exceptions.py (Contains custom error codes/exceptions for SmsCampaignBase)
            ├── handy_functions.py (handy functions for this service)
            ├── sms_campaign_app_constants.py (constants used in this service)
            ├── sms_campaign_base.py (Contains SMsCampaignBase class inherited from CampaignBase class)
            ├── validators.py
        ├── sms_campaign_app/
            ├── api/
                ├── v1_sms_campaign_api.py (SMS campaign API endpoints)
            ├── app.py (Registration of API blueprint)
        ├── tests/ (Contains tests for this service)
        ├── run.py (App runner)
        ├── run_celery.py (Celery App runner)



### SmsCampaignBase Class

We have defined a class SmsCampaignBase which inherits from CampaignBase class

### CampaignBase Class

We use a base class **CampaignBase** defined under _app_common/campaign_services/campaign_base.py_.


### Creating a Campaign

_https://sms-campaign-service/v1/campaign_ with HTTP POST request is the
endpoint to create an SMS campaign for user.
It uses _save()_ method of CampaignBase class.

### Updating a Campaign

_https://sms-campaign-service/v1/campaign/:id_ with HTTP PUT request is the
endpoint to update an SMS campaign for user.
It uses _update()_ method of CampaignBase class.

### Get all Campaigns of a user

_https://sms-campaign-service/v1/campaign_ with HTTP GET request is the
endpoint to get all SMS campaigns of a user.
It uses _get_all_campaigns()_ method of SmsCampaignBase class.

### Get one Campaign

_https://sms-campaign-service/v1/campaign/:id_ with HTTP GET request is the
endpoint to get all SMS campaigns of a user.

### Deleting all Campaigns of a user

_https://sms-campaign-service/v1/campaign_ with HTTP DELETE request is the
endpoint to delete all the SMS campaigns of a user.
It uses _delete()_ method of CampaignBase class.

### Deleting a Campaign

_https://sms-campaign-service/v1/campaign/:id_ with HTTP DELETE request is the
endpoint to delete an SMS campaign for user.
It uses _delete()_ method of CampaignBase class.

### Scheduling a Campaign

_https://sms-campaign-service/v1/campaign/:id/schedule_ with HTTP POST request is the
endpoint to schedule an SMS campaign.
It uses _schedule()_ method of CampaignBase class.

### Re-scheduling a Campaign

_https://sms-campaign-service/v1/campaign/:id/schedule_ with HTTP PUT request is the
endpoint to re-schedule an SMS campaign.
It uses _reschedule()_ method of CampaignBase class.

### Un-scheduling a Campaign

_https://sms-campaign-service/v1/campaign/:id/schedule_ with HTTP POST request is the
endpoint to schedule a. SMS campaign.
It uses _schedule()_ method of CampaignBase class.

### Sending a Campaign

We have a unique Twilio number assigned to a getTalent user which is used to
send SMSs to their candidates. This Twilio number is configured so as to receive the candidates'
reply as well.

We have _https://sms-campaign-service/v1/campaign/:id/send_ for sending a campaign.

Once the campaign is scheduled, _scheduler_service_ will pick it up and will ping the 
endpoint _sms_campaign_service_ at _https://sms-campaign-service/v1/campaign/:id/send_. 
This endpoint will call the **CampaignBase** method _send()_ to fetch the
* smartlist(s) associated with given campaign id (database table **sms_campaign_smartlist**)
* candidates associated with smartlists found in previous step (database table **smartlist_candidate**) 

It then calls _send_campaign_to_candidates()_ and for each candidate found in step-2, it will 
create a Celery task so that campaign can be sent to candidates asynchronously.

For each candidate, we call _send_campaign_to_candidate()_ to send the campaign.
There are some size limitations when sending out SMSs.
For that we use Google's URL shortener API to shorten the required URL before 
sending the campaign to the candidate.

The redirection URL looks like
    http://127.0.0.1:8012/v1/redirect/1052?valid_until=1453990099.0&
        auth_user=no_user&extra=&signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D.
        
This URL is shortened, and candidate gets something similar to **http://goo.gl/SvT76z.**


### Receiving response of candidate via SMS

We have a unique Twilio number assigned to a getTalent user which is used to
send SMS to candidates. This Twilio number is configured so as to receive the candidates'
reply.

We set the callback URL for the Twilio number as _https://sms-campaign-service/v1/receive_. This endpoint 
is hit by Twilio's API to notify us that we have received an SMS on some number.

This uses _process_candidate_reply()_ method of SmsCampaignBase class.
This saves candidate's reply in database table 'sms_campaign_reply' and
updates campaign's blast by increasing number of replies.
 

### URL redirection

(Read README.md under _app_common/common/campaign_services/ to read what is URL redirection)

For this we have the endpoint _https://sms-campaign-service/v1/redirect/:id_ where
we call CampaignBase class method url_redirect() to do all the processing and get
the destination_url(URL provided by recruiter for candidate to visit).
We finally redirect the candidate to that URL.


### Get blasts of a campaign

A blast object contains statistics of a campaign. 
i.e. number of sends, replies and clicks.

We have _https://sms-campaign-service/v1/campaigns/:id/blasts_ to get all the
blasts associated with a given campaign id.

### Get sms_campaign_blast of a campaign by blast_id

We have _https://sms-campaign-service/v1/campaigns/:id/blasts/:id_ to get one particular
blast object associated with a given campaign id.

### Get sms_campaign_send objects of a campaign by blast_id

We have _https://sms-campaign-service/v1/campaigns/:id/blasts/:id/sends_ to get sends objects 
for one particular blast object associated with a given campaign id.

### Get sms_campaign_reply objects of a campaign by blast_id

We have _https://sms-campaign-service/v1/campaigns/:id/blasts/:id/replies_ to get replies objects 
for one particular blast object associated with a given campaign id.

### Get all sends objects of a campaign

We have _https://sms-campaign-service/v1/campaigns/:id/sends_ to get all sends objects 
for one particular campaign.

### Get all replies objects of a campaign

We have _https://sms-campaign-service/v1/campaigns/:id/replies_ to get all replies objects 
for one particular campaign.


### Database tables involved

* url_conversion
* user_phone
* candidate
* candidate_phone
* sms_campaign
* sms_campaign_blast
* sms_campaign_send
* sms_campaign_smartlist
* sms_campaign_reply
* sms_campaign_send_url_conversion


### Information / UI flow

#### Creating SMS campaign

User clicks on _Create SMS Campaign_ button. System should show input fields for 
* name
* smartlist selection
* message body
* User can also selects the frequency of the campaign (i.e. to run it daily, or weekly, 
    or monthly or yearly), end date and etc.