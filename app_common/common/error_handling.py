import inspect

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
        self.status_code = None
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


class UnauthorizedError(TalentError):
    @classmethod
    def http_status_code(cls):
        return 401


class NotFoundError(TalentError):
    @classmethod
    def http_status_code(cls):
        return 404


class ForbiddenError(TalentError):
    @classmethod
    def http_status_code(cls):
        return 403


class UnprocessableEntity(TalentError):
    """https://tools.ietf.org/html/rfc4918#section-11.2"""
    @classmethod
    def http_status_code(cls):
        return 422


class ResourceNotFound(TalentError):
    @classmethod
    def http_status_code(cls):
        return 404


def register_error_handlers(app, logger):
    """

    :type app: flask.app.Flask
    :type logger: logging.Logger
    """
    logger.info("Registering error handlers for app %s", app.import_name)

    @app.errorhandler(405)
    def handle_method_not_allowed(ignored):
        return jsonify({'error': {'message': 'Given HTTP method is not allowed on this endpoint'}}), 405

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        logger.warn("Invalid API usage for app %s: %s", app.import_name, response)
        return response, error.http_status_code()

    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        response = jsonify(error.to_dict())
        logger.warn("Requested resource not found for the app %s as: %s", app.import_name, response)
        return response, error.http_status_code()

    @app.errorhandler(ForbiddenError)
    def handle_forbidden(error):
        logger.warn("Unauthorized for app %s", app.import_name)
        response = jsonify(error.to_dict())
        return response, error.http_status_code()

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized(error):
        response = jsonify(error.to_dict())
        logger.warn("Unauthorized for app %s as: %s", app.import_name, response)
        return response, error.http_status_code()

    @app.errorhandler(ResourceNotFound)
    def handle_resource_not_found(error):
        logger.warn("Resource not found for app %s", app.import_name)
        response = jsonify(error.to_dict())
        return response, error.http_status_code()

    @app.errorhandler(ForbiddenError)
    def handle_forbidden(error):
        logger.warn("Forbidden request format for app %s", app.import_name)
        response = jsonify(error.to_dict())
        return response, error.http_status_code()

    @app.errorhandler(UnprocessableEntity)
    def handle_unprocessable(error):
        logger.warn("Unprocessable data for app %s", app.import_name)
        response = jsonify(error.to_dict())
        return response, error.http_status_code()

    @app.errorhandler(500)
    def handle_internal_server_errors(exc):
        if exc.__class__.__name__ == InternalServerError.__name__:  # Why doesn't instanceof() work here?
            # If an InternalServerError is raised by the server code, return its to_dict
            response = exc.to_dict()
        elif isinstance(exc, InternalServerError):
            response = exc.to_dict()
        elif isinstance(exc, Exception):
            # If any other Exception is thrown, return its message
            response = {'error': {'message': "Internal server error: %s" % exc.message}}
        else:
            # This really shouldn't happen -- exc should be an exception
            response = {'error': {'message': "Internal server error"}}
        logger.error("Internal server error for app %s: %s", app.import_name, exc.message)
        return jsonify(response), 500

