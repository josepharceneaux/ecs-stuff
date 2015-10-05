__author__ = 'oamasood'

from flask import jsonify


class TalentError(Exception):
    def __init__(self, error_message=None, error_code=None, additional_error_info=None):
        """

        :type error_message: str
        :type error_code: int
        :type additional_error_info: dict[str, T]
        """
        Exception.__init__(self)
        self.message = error_message
        if error_code is not None:
            self.status_code = error_code
        self.additional_error_info = additional_error_info

    def to_dict(self):
        error_dict = {'error': {}}
        if self.status_code:
            error_dict['error']['code'] = self.status_code
        if self.message:
            error_dict['error']['message'] = self.message
        if self.additional_error_info:
            for field_name, field_value in self.additional_error_info.items():
                error_dict['error'][field_name] = field_value
        return error_dict

    @classmethod
    def http_status_code(cls):
        return 500


class InvalidUsage(TalentError):
    @classmethod
    def http_status_code(cls):
        return 400


class InternalServerError(TalentError):
    @classmethod
    def http_status_code(cls):
        return 500


def register_error_handlers(app, logger):
    """

    :type app: flask.app.Flask
    :type logger: logging.Logger
    """

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.http_status_code
        logger.warn("Invalid API usage for app %s: %s", app.import_name, response)
        return response

    @app.errorhandler(500)
    def handle_internal_server_errors(exc):
        logger.error("Internal server error for app %s: %s", app.import_name, exc)
        return {'error': {'message': "Internal server error. We're looking into it!"}}


