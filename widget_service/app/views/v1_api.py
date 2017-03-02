from flask import Blueprint, request
from widget_service.common.routes import WidgetApi
from widget_service.app.modules.v1_api_handlers import create_widget_candidate
from widget_service.app import logger

mod = Blueprint('widget_api', __name__)

@mod.route(WidgetApi.CREATE_FOR_TALENT_POOL, methods=['POST'])
def widget_post_receiver(talent_pool_hash):
    """ Post receiver for processing widget date.
    :param talent_pool_hash: (string) the domain attr associated with a WidgetPage.
    :return: A success or error message to change the page state of a widget.
    """
    logger.info('WidgetService::Intake - {}'.format(talent_pool_hash))
    form = request.form
    return create_widget_candidate(form, talent_pool_hash)