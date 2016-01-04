import json

from flask import render_template
from werkzeug.utils import redirect

from push_campaign_service.push_campaign_app import init_push_notification_app, logger
from push_campaign_service.common.models.misc import UrlConversion
from push_campaign_service.common.models.push_notification import PushCampaignBlast

app, celery_app = init_push_notification_app()

from api.v1_push_notification_api import push_notification_blueprint

app.register_blueprint(push_notification_blueprint)


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/url_hits/<int:url_id>')
def url_hit_counts(url_id):
    url_obj = UrlConversion.get_by_id(url_id)
    # source url is actually json dumps data which contains info about candidate, campaign and blast
    data = json.loads(url_obj.source_url)
    # data will be something like
    # {
    #    campaign_id: 12,
    #    blast_id   : 22,
    #    candidateId: 33
    # }
    campaign_id = data['campaign_id']
    blast_id = data['blast_id']
    candidate_id = data['candidate_id']
    blast_obj = PushCampaignBlast.get_by_id(blast_id)
    sends = blast_obj.sends + 1
    blast_obj.update(sends=sends)
    logger.info('Candidate (id: %s) open the url for Puh Campaign (id: %s)' % (candidate_id, campaign_id))
    return redirect(url_obj.destination_url)
