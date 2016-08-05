from social_network_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs
from social_network_service.social_network_app import app


# Do not scheduler jobs in case of local or jenkins environment.
if app.config[TalentConfigKeys.ENV_KEY] in [TalentEnvs.DEV, TalentEnvs.JENKINS]:
    from social_network_service.social_network_app.restful.v1_importer import schedule_importer_job

    # Schedule RSVP and Event importer general job
    schedule_importer_job()
