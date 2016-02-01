### Directory structure

    ├── app_common/
        
        ├── common/
        
            ├── campaign_services/
            
                ├── campaign_base.py (CampaignBase class)
                
                ├── campaign_utils.py (CampaignUtils class which contains handy functions for CampaignBase)
                
                ├── common_tests.py (CampaignCommonTests  class which contains common tests functions for campaigns)
                
                ├── custom_errors.py (Contains custom error codes for CampaignBase)
                
                ├── validators.py (Contains validators required for CampaignBase)


# CampaignBase Class

All campaigns share some functionality, some of which are 

* Creating any type of campaign requires 
    1) name of campaign
    2) body_text
    3) smartlist_ids
* All campaigns need to be scheduled/un-scheduled
* All campaigns have url_redirection process to redirect the candidate to our app when they click
   on a URL received via email, SMS or Push notification etc.
   
So keeping in view all this, we have defined a common class **CampaignBase** under 
_app_common/common/campaign_services/campaign_base.py_.

# Requirements for a new campaign
In case we have a new campaign called _abc_, then

## Model File
* All of its models will go under _app_common/common/models/abc_campaign.py_

## Model Classes
* In _abc_campaign.py_ the following Model classes should exist

    * AbcCampaign()
    * AbcCampaignBlast()
    * AbcCampaignSend()
    * AbcCampaignSmartlist()
    * AbcCampaignSendUrlConversion()
All these classes should have __tablename__ property with class name in snake_case
e.g for AbcCampaign() __tablename__ = 'abc_campaign'

## Relationships
* _AbcCampaign()_ has the following relationship(s)
    * **blast** with model **AbcCampaignBlast()** (backref **campaign**)
    * **smartlists** with database table **AbcCampaignSmartlist()** (backref **campaign**)

* _AbcCampaignBlast()_ has relationship(s)
    * **blast_sends** with model **AbcCampaignSend()** (backref **blast**)
    
* _AbcCampaignSend()_ has relationship(s)
    * **url_conversions** with model **AbcCampaignSendUrlConversion()** (backref **send**)

* AbcCampaignSmartlist()

* _AbcCampaignSendUrlConversion()_ has relationship(s)
    * **abc_campaign_sends_url_conversions** in model **UrlConversion()** (backref **url_conversion**)
 

For a deeper understanding, you can refer to the models found in the _models/sms_campaign.py_ or _models/push_campaign.py_ files.

### Creating a Campaign

We have _save()_ method of CampaignBase class to create/save a campaign in database.

_save()_ gets the data from UI and saves the campaign in the database in a respective campaign's 
table e.g  "sms_campaign" or "push_campaign" etc. depending upon the campaign type. 
It performs the following steps:

* Validates the form data, gets the campaign model and invalid_smartlist_ids if any
* Saves the campaign in the database
* Adds entries in the campaign_smartlist table (e.g. "sms_campaign_smartlist" etc)
* Creates activity for that by calling create_activity_for_campaign_creation()
    (e.g "'Harvey Specter' created an SMS campaign: 'Hiring at getTalent'")

### Updating a Campaign

We have _update()_ method of CampaignBase class to update already saved campaign in database.

_update()_ will will update the existing record.        
It does following steps:

* Validates if logged-in user is the owner/creator of given campaign_id and gets the
    campaign object
* Validates UI data
* Updates the respective campaign record in database
        
### Deleting a Campaign

We have _delete()_ method of CampaignBase class to delete a campaign.
This function is used to delete the campaign in following given steps.

* Validates that current user is an owner of given campaign id and gets

    * campaign object and 2) scheduled task from scheduler_service.
    
* If campaign is scheduled, then do the following steps:

    * Calls get_authorization_header() to get auth header (which is used to make
        HTTP request to scheduler_service)
    * Makes HTTP DELETE request to scheduler service to remove the job from redis job
        store.
        
    (If both of these two steps are successful, it returns True, otherwise returns False.)
   
* Deletes the campaign from database and returns True if campaign is deleted successfully.
    Otherwise it returns False.


### Scheduling a Campaign

We have _schedule()_ method of CampaignBase class to schedule a campaign.
This actually sends a POST request to the scheduler_service to schedule a given task. We set the URL (on which 
scheduler_service will hit when the time comes to run that Job) in child class and call super 
constructor to make HTTP POST call to scheduler_service.

### Re-Scheduling a Campaign

We have _reschedule()_ method of CampaignBase class to re-schedule a campaign.

* Calls data_validation_for_campaign_schedule() to validate UI data
* Calls pre_process_re_schedule() to check if task is already scheduled with given
    data or we need to schedule new one.
* If we need to schedule again, we call schedule() method.

### Un-Scheduling a Campaign

We have _unschedule()_ method of CampaignBase class to unschedule a campaign.

This function gets the campaign object, and checks if it is present in the scheduler_service.
If the campaign is present in the scheduler_service, we delete it there and on success we return the
campaign object, otherwise we return None.

### Sending a Campaign

We have _send()_ method of CampaignBase class for sending a campaign.

Once the campaign is scheduled,the _scheduler_service_ will pick it up and will ping the 
respective endpoint. 
(e.g for_sms_campaign_service_ at _https://sms-campaign-service/v1/campaign/:id/send_.) 
This endpoint will call the **CampaignBase** method _send()_ to fetch the

* smartlist(s) associated with given campaign id (database table **sms_campaign_smartlist**)
* candidates associated with smartlists found in previous step (database table **smartlist_candidate**) 

It then calls _send_campaign_to_candidates()_ and for each candidate found in step-2, it will 
create a Celery task so that the campaign can be sent to the candidates asynchronously.
For each candidate, _send_campaign_to_candidate()_ will be called which will
be implemented by child classes.

 
### URL redirection

When a campaign is sent to a candidate and the recruiter wants the candidate to visit a web page, 
we need a URL redirection mechanism so that when candidate clicks on a URL present in any 
campaign (e.g. in SMS, Email etc),they are redirected to our app first so that we can keep a
track of the number of clicks,the hit_count and to create activity 
(e.g. Mitchel clicked on SMS campaign 'Jobs'.)

Let's say a recruiter wants the candidates to visit https://www.gettalent.com/jobs.
So, we
 
* First save this as destination_url in database table "url_conversion" with empty source_url, 
    and get the id of record. Suppose id comes to be "1052". 
* Create a URL (e.g for SMS campaign) http://127.0.0.1:8012/v1/redirect/1052.
* Sign this URL by using CampaignUtils 
(defined in _app_common/common/campaign_services/campaign_utils.py_) method sign_redirect_url()
After adding the signature,the URL looks like
    http://127.0.0.1:8012/v1/redirect/1052?valid_until=1453990099.0&
        auth_user=no_user&extra=&signature=cWQ43J%2BkYetfmE2KmR85%2BLmvuIw%3D.
        
In case of SMS campaigns, this URL is shortened, and the candidate gets something similar to 
**http://goo.gl/SvT76z.**

So, when the candidate clicks on this shortened URL,the API endpoint
/v1/redirect/ with url_conversion_id 1052 is hit.

**How to use this method?**

We need to pass the url_conversion id and the name of the campaign as 
    CampaignBase.url_redirect(1, 'sms_campaign')
    
You can see an example of this in the SmsCampaignUrlRedirection() Class in 
sms_campaign_service/sms_campaign_app/v1_sms_campaign_api.py

**Functionality**

From a given url_conversion_id, this method

* Gets the "url_conversion" object from the database
* Gets the campaign_send_url_conversion object (e.g. "sms_campaign_send_url_conversion" object)
    from database
* Gets the campaign_blast object (e.g "sms_campaign_blast" object) using SQLAlchemy relationship
    from object found in step-2
* Gets the candidate object using SQLAlchemy relationship from object found in step-2
* Validates if all the objects (found in steps 2,3,4)are present in database
* If the destination URL of the object found in step-1 is empty, it raises an invalid usage error.
    Otherwise we move on to update the statistics.
* Calls update_stats_and_create_click_activity() class method to do the following:
    * Increase "hit_count" by 1 for "url_conversion" record.
    * Increase "clicks" by 1 for "sms_campaign_blast" record.
    * Add activity that abc candidate clicked on xyz campaign.
        "'Alvaro Oliveira' clicked URL of campaign 'Jobs at Google'"
* Returns the destination URL (actual URL provided by recruiter(user)
    where we want our candidate to be redirected.

In case of any exception raised, it must be gracefully handled and the candidate should only get
 an internal server error message.

### Database tables involved

* user
* token
* frequency
* url_conversion
* smart_list
* smart_list_candidate