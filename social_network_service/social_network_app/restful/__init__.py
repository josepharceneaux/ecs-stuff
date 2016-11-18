from ...tasks import import_meetup_rsvps
from social_network_service.social_network_app import app
from social_network_service.common.talent_config_manager import TalentConfigKeys, TalentEnvs


# Do not schedule jobs in case of local or jenkins environment.
if app.config[TalentConfigKeys.ENV_KEY] not in [TalentEnvs.JENKINS]:
    from social_network_service.social_network_app.restful.v1_importer import schedule_importer_job
    # Schedule RSVP and Event importer general job
    schedule_importer_job()
    import_meetup_rsvps()
