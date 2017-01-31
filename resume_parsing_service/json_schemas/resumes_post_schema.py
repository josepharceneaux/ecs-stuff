"""JSON schema(s) used by the resume parsing service."""


"""
Create Candidate from resume stored in FilePicker
Endpoint:
    /parse_resume
Documentation:
    http://docs.gettalentresumeparsingservice.apiary.io/#reference/0/resume-parsing-service/parse-a-candidate-resume-web/json.
"""
create_candidate_schema = {
    'type': 'object',
    'properties': {
        'create_candidate': {'type': ['boolean', 'null']},
        'filename': {'type': ['string', 'null']},
        'filepicker_key': {'type': 'string'},
        'source_id': {'type': 'integer'},
        'source_product_id': {'type': 'integer'},
        'talent_pools': {'type': ['array', 'null']}
    },
    'required': ['filepicker_key']
}
