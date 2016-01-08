# Resume Service
Flask microservice for handling resume parsing.
Served on port 8003

## Oauth
This service requires Oauth2 and forwards the token from a requesting client to the auth server. That is, this service is not a registered client in the database.

## TODOS
Pylint reports that parselib in general has too many branches and statements. It would be good to break up some of the larger functions.
optic_parse_lib.parse_candidate_experiences has too many locals.
Improve general exceptions.
OCR is huge bottleneck/opportunity.
Test for candidate already exists on /parse endpoint
Test for candidate already exists on /batch endpoint
Contemplate opportunities for Exceptions and handle appropriately (OCR/BG/candidate_service down).