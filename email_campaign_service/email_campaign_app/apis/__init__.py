from email_campaign_service.email_campaign_app import app
from email_campaign_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs


# Do not schedule jobs in case of local or jenkins environment.
if app.config[TalentConfigKeys.ENV_KEY] not in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
    from email_campaign_service.email_campaign_app.apis.email_clients import schedule_job_for_email_conversations

    # Schedule job for getting email-conversations
    schedule_job_for_email_conversations()

