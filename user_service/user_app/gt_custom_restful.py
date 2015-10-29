__author__ = 'ufarooqi'
from flask_restful import (Api, reqparse)


class GetTalentApi(Api):
    """
    Flask uses its own error handler so we are overwriting his error handler with
    our customized error handler
    """
    def error_router(self, original_handler, e):
        return original_handler(e)
