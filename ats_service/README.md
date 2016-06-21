# ATS Service
*Flask micro service for interfacing with Applicant Tracking Systems.*

### API Version 1

#### API List

- List each ATS we have integrated with
    + `/v1/ats-list [GET]`
- Register ATS account for a user with an ATS
    + `/v1/ats-register/:credentials [POST]`
- Decomission ATS account for a user with an ATS
    + `/v1/ats-unregister/:account_id [DELETE]`
- Retrieve all ATS accounts for a user
    + `/v1/ats-user-accounts [GET]`
- Retrieve all ATS candidates associated with an ATS account
    + `/v1/ats-candidates/:account_id [GET]`
- Refresh all ATS candidates from an ATS account
    + `/v1/ats-refresh/:account_id [GET]`
- Link getTalent candidate to ATS candidate
    + `/v1/ats-link/:candidate_id/:ats_candidate_id [PUT]`

#### Error Codes

#### Authentication

Like other getTalent services, ATS service uses oAuth2 for user authentication. See [AuthService](https://github.com/gettalent/talent-flask-services/blob/master/auth_service/README.md) for more information.

Authentication to an ATS varies by ATS but is done using a user's account with that ATS.

### Database Schema

![Image Missing](ATS_erd.png?raw=true "Database Schema")
