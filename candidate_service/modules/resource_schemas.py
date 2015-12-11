from candidate_service.common.error_handling import InvalidUsage


def validate_request_body_keys(request_body):
    assert isinstance(request_body, dict)
    valid_keys = ['id',
                  'last_name',
                  'addresses',
                  'areas_of_interest',
                  'phones',
                  'educations',
                  'emails',
                  'custom_fields',
                  'preferred_locations',
                  'first_name',
                  'middle_name',
                  'military_services',
                  'social_networks',
                  'skills',
                  'work_experiences',
                  'work_preference']

    keys = request_body.keys()
    for key in keys:
        if key not in valid_keys:
            raise InvalidUsage(error_message="Invalid key/field: {}".format(key))


# def format_inputs(user, request_body):
#     formatted_dict = dict(user_id=user.id,
#                           addresses=request_body.get('addresses'),
#                           first_name=request_body.get('first_name'),
#                           last_name=request_body.get('last_name'),
#                           full_name=request_body.get('full_name'),
#                           phones=request_body.get('phones'),
#                           educations=request_body.get('educations'),
#                           military_services=request_body.get('military_services'),
#                           social_networks=request_body.get('social_networks'),
#                           work_experiences=request_body.get('work_experiences'),
#                           work_preference=request_body.get('work_preference'),
#                           preferred_locations=request_body.get('preferred_locations'),
#                           skills=request_body.get('skills'))
#
#     phones = request_body.get('phones')
#     if phones:
#         valid_keys = ['is_default', 'value', 'label']
#         for phone in phones:
#             keys = phone.keys()
#             for key in keys:
#                 if key not in valid_keys:
#                     raise InvalidUsage(error_message="Invalid key in candidate's phone-dict: {}".format(key))
#
#     educations = request_body.get('educations')
#     if educations:
#         valid_keys = ['school_type', 'school_name', 'city', 'state', 'country', 'is_current', 'degrees']
#         for education in educations:
#             degrees = education.get('degrees')
#             if degrees:
#                 valid_keys = ['type', 'title', 'gpa_num', 'start_year', 'start_month', 'end_year', 'end_month', 'bullets']
#                 for degree in degrees:
#                     bullets = degree.get('bullets')
#                     if bullets:
#                         valid_keys = ['major', 'comments']
#                         for bullet in bullets:
#                             keys = bullet.keys()
#                             for key in keys:
#                                 if key not in valid_keys:
#                                     raise InvalidUsage(error_message="Invalid key in education-degree-bullet: {}".format(key))
#                     keys = degree.keys()
#                     for key in keys:
#                         if key not in valid_keys:
#                             raise InvalidUsage(error_message="Invalid key in education-degree: {}".format(key))
#             keys = education.keys()
#             for key in keys:
#                 if key not in valid_keys:
#                     raise InvalidUsage(error_message="Invalid key in candidate's education-dict: {}".format(key))


