# SMSCampaignService
Flask microservice for handling SMS campaigns of user


# Create a campaign
For creating campaign, UI will request the resource at /v1/campaigns with POST request

# Schedule a campaign

1- If user wants to schedule the created campaign, UI will request the resource at 
    /v1/campaigns/:id/schedule with POST request.
    
2- If campaign was scheduled already and user wants to schedule it again, UI will request the 
    resource at /v1/campaigns/:id/schedule with PUT request  