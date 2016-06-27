# Candidate Service
*Flask micro service for handling the candidate resources.*
## Authentication
Candidate service uses oAuth2 for user authentication. See [AuthService](https://github.com/gettalent/talent-flask-services/blob/master/auth_service/README.md) for more information.
## APIs
##### Version
1
#### API DOCS
- [Candidate](http://docs.gettalentcandidateservice.apiary.io/#reference/candidate)
- [Candidates](http://docs.gettalentcandidateservice.apiary.io/#reference/candidates)
- [Search](http://docs.gettalentcandidateservice.apiary.io/#reference/search)
- [Tags](http://docs.candidatetags.apiary.io/#reference/tags)
- [Pipelines](http://docs.candidatetags.apiary.io/#reference/pipelines)
- [References](http://docs.candidatetags.apiary.io/#reference/candidate-references)

##### Custom Error Codes
All custom error codes are in the 3000s range. Please see [this file](https://github.com/gettalent/talent-flask-services/blob/develop/candidate_service/custom_error_codes.py).
