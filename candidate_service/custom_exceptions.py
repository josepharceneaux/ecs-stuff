"""
Custom error codes for all candidate-REST-resources
"""
# General error codes
INVALID_INPUT = 3000
MISSING_INPUT = 3001

# Error codes for Candidate(s)
CANDIDATE_NOT_FOUND = 3010
CANDIDATE_IS_HIDDEN = 3011
CANDIDATE_FORBIDDEN = 3013
CANDIDATE_ALREADY_EXISTS = 3014
INVALID_EMAIL = 3015

# Error codes for CandidateAddress(s)
ADDRESS_NOT_FOUND = 3030
ADDRESS_FORBIDDEN = 3031

# Error codes for CandidateAreaOfInterest
AOI_FORBIDDEN = 3040
AOI_NOT_FOUND = 3041

# Error codes for CandidateCustomField
CF_FORBIDDEN = 3050
CF_NOT_FOUND = 3051

# Error codes for CandidateEducation, CandiadteEducationDegree, and CandidateEducationDegreeBullet
EDUCATION_FORBIDDEN = 3060
EDUCATION_NOT_FOUND = 3061
DEGREE_FORBIDDEN = 3062
DEGREE_NOT_FOUND = 3063
DEGREE_BULLET_FORBIDDEN = 3064
DEGREE_BULLET_NOT_FOUND = 3065

# Error codes for CandidateExperience & CandidateExperienceBullet
EXPERIENCE_FORBIDDEN = 3070
EXPERIENCE_NOT_FOUND = 3071
EXPERIENCE_BULLET_FORBIDDEN = 3072
EXPERIENCE_BULLET_NOT_FOUND = 3073

# Error codes for CandidateEmail
EMAIL_FORBIDDEN = 3080
EMAIL_NOT_FOUND = 3081

# Error codes for CandidateMilitaryService
MILITARY_FORBIDDEN = 3090
MILITARY_NOT_FOUND = 3091

# Error codes for CandidatePhone
PHONE_FORBIDDEN = 3100
PHONE_NOT_FOUND = 3101

# Error codes for CandidatePreferredLocation
PREFERRED_LOCATION_FORBIDDEN = 3110
PREFERRED_LOCATION_NOT_FOUND = 3111

# Error codes for CandidateSkill
SKILL_FORBIDDEN = 3120
SKILL_NOT_FOUND = 3121

# Error codes for CandidateSocialNetwork
SN_FORBIDDEN = 3130
SN_NOT_FOUND = 3131

# Error codes for CandidateWorkPreference
WORK_PREF_FORBIDDEN = 3140
WORK_PREF_NOT_FOUND = 3141

