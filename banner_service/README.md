# Banner Service

CRD Application for creating Global Banners (WEB-1302)

A TALENT_ADMIN only set of CRD routes for global banners.

Banner attributes are stored in Redis and published to the PubNub channel 'banners'

Logic for showing a banner is front end specific.

Another set of CR endpoints will determine is a user has seen a certain banner (60 day expire in redis).