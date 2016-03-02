from candidate_service.candidate_app import logger
from candidate_service.common.error_handling import InternalServerError
from candidate_service.modules.talent_cloud_search import _cloud_search_domain_connection


try:
    _cloud_search_domain_connection()
    logger.info("connection to cloud-search successful")
except Exception:
    raise InternalServerError("connection to cloud search failed")