from talentbot_service.common.models.user import User

print User.generate_jw_token(user_id=5000)
