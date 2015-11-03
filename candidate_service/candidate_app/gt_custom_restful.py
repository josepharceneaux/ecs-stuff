__author__ = 'amirhb'

from flask_restful import Api


class GetTalentApi(Api):
    """
    Flask uses its own error handler so we are overwriting its error handler with
    our customized error handler
    """
    def error_router(self, original_handler, e):
        return original_handler(e)
