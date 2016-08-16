"""
Custom error codes for all candidate-REST-resources
"""


class CandidateCustomErrors(object):
    # General error codes
    INVALID_INPUT = 3000
    MISSING_INPUT = 3001
    INVALID_USAGE = 3002

    # Error codes for Candidate(s)
    CANDIDATE_NOT_FOUND = 3010
    CANDIDATE_IS_HIDDEN = 3011
    CANDIDATE_FORBIDDEN = 3012
    CANDIDATE_ALREADY_EXISTS = 3013

    # Error codes for CandidateAddress(s)
    ADDRESS_NOT_FOUND = 3020
    ADDRESS_FORBIDDEN = 3021

    # Error codes for CandidateAreaOfInterest
    AOI_FORBIDDEN = 3030
    AOI_NOT_FOUND = 3031

    # Error codes for CandidateCustomField
    CUSTOM_FIELD_FORBIDDEN = 3040
    CUSTOM_FIELD_NOT_FOUND = 3041

    # Error codes for CandidateEducation, CandidateEducationDegree, and CandidateEducationDegreeBullet
    EDUCATION_FORBIDDEN = 3050
    EDUCATION_NOT_FOUND = 3051
    DEGREE_FORBIDDEN = 3052
    DEGREE_NOT_FOUND = 3053
    DEGREE_BULLET_FORBIDDEN = 3054
    DEGREE_BULLET_NOT_FOUND = 3055

    # Error codes for CandidateExperience & CandidateExperienceBullet
    EXPERIENCE_FORBIDDEN = 3060
    EXPERIENCE_NOT_FOUND = 3061
    EXPERIENCE_BULLET_FORBIDDEN = 3062
    EXPERIENCE_BULLET_NOT_FOUND = 3063

    # Error codes for CandidateEmail
    EMAIL_FORBIDDEN = 3070
    EMAIL_NOT_FOUND = 3071
    INVALID_EMAIL = 3072

    # Error codes for CandidateMilitaryService
    MILITARY_FORBIDDEN = 3080
    MILITARY_NOT_FOUND = 3081
    MILITARY_INVALID_DATE = 3082

    # Error codes for CandidatePhone
    PHONE_FORBIDDEN = 3090
    PHONE_NOT_FOUND = 3091
    PHONE_EXISTS = 3092
    INVALID_PHONE = 3093

    # Error codes for CandidatePreferredLocation
    PREFERRED_LOCATION_FORBIDDEN = 3100
    PREFERRED_LOCATION_NOT_FOUND = 3101

    # Error codes for CandidateSkill
    SKILL_FORBIDDEN = 3110
    SKILL_NOT_FOUND = 3111

    # Error codes for CandidateSocialNetwork
    SOCIAL_NETWORK_FORBIDDEN = 3120
    SOCIAL_NETWORK_NOT_FOUND = 3121

    # Error codes for CandidateWorkPreference
    WORK_PREF_FORBIDDEN = 3130
    WORK_PREF_NOT_FOUND = 3131
    WORK_PREF_EXISTS = 3132

    # Error codes for CandidatePreference
    PREFERENCE_FORBIDDEN = 3140
    PREFERENCE_NOT_FOUND = 3141
    NO_PREFERENCES = 3142
    PREFERENCE_EXISTS = 3143

    # Error codes for CandidatePhoto
    PHOTO_NOT_FOUND = 3150
    PHOTO_FORBIDDEN = 3151

    # Error codes for CandidateLanguage
    LANGUAGE_NOT_FOUND = 3160
    LANGUAGE_FORBIDDEN = 3161

    # Error codes for Candidate Reference
    REFERENCE_NOT_FOUND = 3160
    REFERENCE_FORBIDDEN = 3161
    REFERENCE_EXISTS = 3162

    # Error codes for Candidate Tags
    TAG_NOT_FOUND = 3170
    TAG_FORBIDDEN = 3172
    TAG_EXISTS = 3173

    # Error codes for Candidate Source
    INVALID_SOURCE_ID = 3180
    INVALID_SOURCE_PRODUCT_ID = 3181

    # Error codes for Candidate Notes
    NOTE_NOT_FOUND = 3290
    NOTE_FORBIDDEN = 3291
