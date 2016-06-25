# ATS Service
*Flask micro service for interfacing with Applicant Tracking Systems.*

### API Version 1

#### API List

- List each ATS we have integrated with
    + `/v1/ats [GET]`
- Register ATS account for a user with ATS credentials
    + `/v1/ats-accounts/:id [POST]`
- Decomission an ATS account for a user
    + `/v1/ats-accounts/:id/:account_id [DELETE]`
- Retrieve all ATS accounts belonging to a user
    + `/v1/ats-accounts/:id [GET]`
- Update a GT ATS account from the the ATS itself
    + `/v1/ats-candidates/refresh/:account_id/ [GET]`
- Retrieve all ATS candidates (stored locally) associated with an ATS account
    + `/v1/ats-candidates/:account_id [GET]`
- Link getTalent candidate to ATS candidate
    + `/v1/ats-candidates/:candidate_id/:ats_candidate_id [POST]`
- Unlink getTalent candidate from ATS candidate
    + `/v1/ats-candidates/:candidate_id/:ats_candidate_id [DELETE]`

#### Error Codes

#### Authentication

Like other getTalent services, ATS service uses oAuth2 for user authentication. See [AuthService](https://github.com/gettalent/talent-flask-services/blob/master/auth_service/README.md) for more information.

Authentication to an ATS varies by ATS but is done using a user's account with that ATS.

### Database Schema

![Image Missing](ATS_erd.png?raw=true "Database Schema")
