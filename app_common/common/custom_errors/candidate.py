"""
File contains custom error codes & messages for candidate service.
Candidate service's custom error codes range from 1200 to 1299
"""
# General errors -- 1200 - 1209
NOT_FOUND = ('Candidate not found', 1200)
IS_ARCHIVED = ('Candidate is archived', 1201)
CANDIDATE_FORBIDDEN = ('Not authorized to access candidate', 1202)
ARCHIVE_NOT_ALLOWED = ('Not authorized to archive candidate', 1203)

# Address -- 1210 - 1214
ADDRESS_NOT_FOUND = ('Candidate address not found', 1210)
ADDRESS_FORBIDDEN = ('Unauthorized candidate address', 1211)

# Custom fields

# Education -- 1215 - 1219
EDUCATION_NOT_FOUND = ('Candidate education not found', 1215)
EDUCATION_FORBIDDEN = ('Unauthorized candidate education', 1216)

# Emails -- 1220 - 1224
INVALID_EMAIL = ('Invalid email address(es)', 1220)

# Military services -- 1225 - 1229

# Phones -- 1230 - 1234

# Skills -- 1235 - 1239
SKILL_NOT_FOUND = ('Candidate skill not found', 1235)
SKILL_FORBIDDEN = ('Unauthorized candidate skill', 1236)

# Social Networks -- 1240 - 1244

# Talent pools -- 1245 - 1249

# Work preference -- 1250 - 1254
PREFERENCE_NOT_FOUND = ('Candidate work preference not found', 1250)
PREFERENCE_FORBIDDEN = ('Unauthorized candidate work preference', 1251)
