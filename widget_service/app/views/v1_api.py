from flask import Blueprint, request
from widget_service.app import logger
from widget_service.app.modules.v1_api_handlers import create_widget_candidate
from widget_service.common.error_handling import InvalidUsage
from widget_service.common.routes import WidgetApi

mod = Blueprint('widget_api', __name__)


@mod.route(WidgetApi.CREATE_FOR_TALENT_POOL, methods=['POST'])
def widget_post_receiver(talent_pool_hash):
    """ Post receiver for processing widget date.
    :param talent_pool_hash: (string) the domain attr associated with a WidgetPage.
    :return: A success or error message to change the page state of a widget.
    """
    form = request.form
    if not form:
        return InvalidUsage(error_message='No form supplied')
    logger.info('WidgetService::Intake - TP:{}'.format(talent_pool_hash))
    return create_widget_candidate(form, talent_pool_hash)
