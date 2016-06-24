
# Database connection and logger
from sqlalchemy.sql import text
from candidate_service.common.models.db import db
from candidate_service.common.models.talent_pools_pipelines import TalentPoolCandidate
from candidate_service.candidate_app import logger


def calculate_candidate_engagement_score(candidate_id):
    """
    This method will calculate the average candidate engagement score of a candidate
    :param candidate_id: Id of candidate
    :return: Average Engagement score of a candidate
    :rtype: Float|None
    """

    talent_pool_ids_of_candidate = TalentPoolCandidate.query.with_entities(
            TalentPoolCandidate.talent_pool_id).filter(TalentPoolCandidate.candidate_id == candidate_id).all()
    talent_pool_ids_of_candidate = [talent_pool_id_of_candidate.talent_pool_id for
                                    talent_pool_id_of_candidate in talent_pool_ids_of_candidate]

    sql_query = """
    SELECT avg(average_engagement_score.average_engagement_score_of_pipeline) AS engagement_score
    FROM
      (SELECT avg(engagement_score_of_all_campaigns.engagement_score) as average_engagement_score_of_pipeline
      FROM
       (SELECT email_campaign_send.EmailCampaignId,
               email_campaign_send_url_conversion.EmailCampaignSendId,
               CASE WHEN sum(url_conversion.HitCount) = 0 THEN 0.0 WHEN sum(email_campaign_send_url_conversion.type * url_conversion.HitCount) > 0 THEN 100 ELSE 33.3 END AS engagement_score
        FROM email_campaign_send
        INNER JOIN email_campaign_send_url_conversion ON email_campaign_send.Id = email_campaign_send_url_conversion.EmailCampaignSendId
        INNER JOIN url_conversion ON email_campaign_send_url_conversion.UrlConversionId = url_conversion.Id
        WHERE email_campaign_send.candidateId = :candidate_id
        GROUP BY email_campaign_send_url_conversion.EmailCampaignSendId) AS engagement_score_of_all_campaigns
      NATURAL JOIN email_campaign_smart_list
      INNER JOIN smart_list ON smart_list.Id = email_campaign_smart_list.SmartListId
      INNER JOIN talent_pipeline ON talent_pipeline.id = smart_list.talentPipelineId
      WHERE talent_pipeline.id IS NOT NULL AND talent_pipeline.talent_pool_id IN :talent_pool_ids
      GROUP BY talent_pipeline.id) as average_engagement_score;
    """

    try:
        engagement_score = db.session.connection().execute(text(sql_query), candidate_id=candidate_id,
                                                           talent_pool_ids=tuple(talent_pool_ids_of_candidate))
        result = engagement_score.fetchone()
        if not result or not result['engagement_score']:
            return None
        else:
            return float(str(result['engagement_score']))
    except Exception as e:
        logger.exception("Couldn't compute engagement score for candidate(%s) because (%s)" % (candidate_id, e.message))
        return None
