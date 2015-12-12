from sms_campaign_service.modules.celery_config import send_scheduled_campaign, tsum
from celery import chord
import time
if __name__ == '__main__':
    print 'before execution'
    callback = tsum.subtask()
    header = [send_scheduled_campaign.subtask() for i in xrange(0, 50)]
    chord(header)(callback)
    print 'after execution'
