"""
File contains custom error codes & messages for user service.
User service's custom error codes range from 1300 to 1399
"""
FORBIDDEN_CUSTOM_FIELDS = ("Custom field IDs must belong to user's domain", 1301)
TP_NOT_FOUND = ("Talent pool ID(s) not recognized", 1302)
TP_FORBIDDEN_1 = ("Talent pool does not belong to user's domain", 1303)
TP_FORBIDDEN_2 = ("Talent pool does not belong to user's user group", 1304)
INVALID_SP_ID = ("Source Product ID not recognized", 1305)
