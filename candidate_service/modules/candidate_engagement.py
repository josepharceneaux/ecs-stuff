
# Database connection and logger
from sqlalchemy.sql import text
from candidate_service.common.models.db import db
from candidate_service.candidate_app import logger


def calculate_candidate_engagement_score(candidate_id):
    """
    This method will calculate the average candidate engagement score of a candidate
    :param candidate_id: Id of candidate
    :return: Average Engagement score of a candidate
    :rtype: Float|None
    """
    sql_query = """
    SELECT avg(average_engagement_score.average_engagement_score_of_pipeline) AS engagement_score
    FROM
      (SELECT avg(engagement_score_of_pipeline.engagement_score) AS average_engagement_score_of_pipeline
       FROM
         (SELECT smart_list.talentPipelineId,
                 engagement_score_for_all_pipelines.EmailCampaignId,
                 engagement_score_for_all_pipelines.engagement_score
          FROM
            (SELECT engagement_score_of_all_campaigns.EmailCampaignId,
                    avg(engagement_score_of_all_campaigns.engagement_score) AS engagement_score
             FROM
               (SELECT email_campaign_send.EmailCampaignId,
                       email_campaign_send_url_conversion.EmailCampaignSendId,
                       CASE WHEN sum(url_conversion.HitCount) = 0 THEN 0.0 WHEN sum(email_campaign_send_url_conversion.type * url_conversion.HitCount) > 0 THEN 100 ELSE 33.3 END AS engagement_score
                FROM email_campaign_send
                INNER JOIN email_campaign_send_url_conversion ON email_campaign_send.Id = email_campaign_send_url_conversion.EmailCampaignSendId
                INNER JOIN url_conversion ON email_campaign_send_url_conversion.UrlConversionId = url_conversion.Id
                WHERE email_campaign_send.candidateId = :candidate_id
                GROUP BY email_campaign_send_url_conversion.EmailCampaignSendId) AS engagement_score_of_all_campaigns
             GROUP BY engagement_score_of_all_campaigns.EmailCampaignId) AS engagement_score_for_all_pipelines
          NATURAL JOIN email_campaign_smart_list
          INNER JOIN smart_list ON smart_list.Id = email_campaign_smart_list.SmartListId
          WHERE smart_list.talentPipelineId IS NOT NULL) AS engagement_score_of_pipeline
       GROUP BY engagement_score_of_pipeline.talentPipelineId) AS average_engagement_score;
    """

    try:
        engagement_score = db.session.connection().execute(text(sql_query), candidate_id=candidate_id)
        result = engagement_score.fetchone()
        if not result or not result['engagement_score']:
            return None
        else:
            return float(str(result['engagement_score']))
    except Exception as e:
        logger.exception("Couldn't compute engagement score for candidate(%s) because (%s)" % (candidate_id, e.message))
        return None
