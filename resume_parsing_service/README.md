# Resume Service
Flask microservice for handling resume parsing.

## Oauth
This service requires Oauth2 and forwards the token from a requesting client to the auth server. That is, this service is not a registered client in the database.

## Application specific config keys that MUST be set:
BG_URL
CONSUMER SECRET
GOOGLE_API_KEY
GOOGLE_CLOUD_VISION_URL
TOKEN_SECRET

## TODOS
Replace Abbyy OCR with ImageMagick via Lambda function.

## Reporting Issues:
Resume Parsing Service should return an [error code](https://gtdice.atlassian.net/wiki/display/PRD/Resume+Parsing+Service) specific to the issue in the response.
Please consult this code to verify that the issue lies in the Resume Parsing Service (not a bad response from Google/Burning Glass/another GT service).

If you believe the issue is with the parsing accuracy please first consult the raw response from Burning Glass. This can be obtained with the `raw_response` key when the `create_mode` is set to `False`. 

When filing a JIRA please includce the following (where applicable):

 * Environment(s) where the error was observed.
 
 * Error code in response or copy/pasted response.

 * Raw Response from Burning Glass.

 * Steps to reproduce.

 * Resume(s) used in generating error.
 
 * `id` of Candidate if error is during update phase.
 
 * Approximate time this issue was discovered (useful for sifting logs).