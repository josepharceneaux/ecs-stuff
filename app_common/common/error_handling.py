"""
This module contains our custom exception types (Errors) and error handlers for these exceptions.

    TalentError is the base class for all other exceptions classes.
"""
from sqlalchemy.orm.exc import DetachedInstanceError
from flask import (jsonify, request, has_request_context)

__author__ = 'oamasood'


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
        return handle_error(error, 'Invalid API usage.')

    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        return handle_error(error, 'Requested resource not found.')

    @app.errorhandler(ForbiddenError)
    def handle_forbidden(error):
        return handle_error(error, 'Forbidden for this resource.')

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized(error):
        return handle_error(error, 'Unauthorized for this resource.')

    @app.errorhandler(ResourceNotFound)
    def handle_resource_not_found(error):
        return handle_error(error, 'Resource not found.')

    @app.errorhandler(UnprocessableEntity)
    def handle_unprocessable(error):
        return handle_error(error, 'Unprocessable data for this resource.')

    @app.errorhandler(500)
    def handle_internal_server_errors(exc):
        if isinstance(exc, InternalServerError):
            error = exc.to_dict()
            response = error
        else:
            error = exc.message
            response = {'error': {'message': "Internal server error"}}
        app_name, url, user_id, user_email = get_request_info(app)
        logger.error("Internal server error. App: %s,\nUrl: %s,\nError Details: %s", app.import_name,
                     request.url if has_request_context() else None, error)
        logger.error('''Internal server error.
                        App: %s,
                        Url: %s
                        User Id: %s
                        UserEmail: %s
                        Error Details: %s
                        ''', app_name, url, user_id, user_email, error)
        return jsonify(response), 500

    def handle_error(error, message):
        """
        This function logs error message which contains app name, Url and error details.
        It also returns response with respective status code.
        :param TalentError error: exception raised by app
        :param str message: message to append while logging error details.
        :return: response, status_code
        """
        message = message if message else 'Error occurred.'
        assert isinstance(error, TalentError), '"error" is not a getTalent custom exception.'
        error_dict = error.to_dict()
        response = jsonify(error_dict)
        app_name, url, user_id, user_email = get_request_info(app)

        logger.warn('''%s
                       App: %s,
                       Url: %s
                       User Id: %s
                       UserEmail: %s
                       Error Details: %s
                       ''', message, app_name, url, user_id, user_email, error_dict)
        return response, error.http_status_code()


def get_request_info(app):
    """
    This function takes app as argument and returns request related information about user, request url and
    error information.
    :param app: Flask app
    :rtype tuple
    """
    # Can't import at top, due to circular dependency, can remove this import if we are 100 % sure
    # that request.user is user instance.
    from ..common.models.user import User
    app_name, url, user_id, user_email = (None,) * 4
    if has_request_context():
        app_name = app.import_name
        url = request.url
        if hasattr(request, 'user') and isinstance(request.user, User):
            try:
                user_id = request.user.id
                user_email = request.user.email
            except DetachedInstanceError:
                user_id = None
                user_email = None
    return app_name, url, user_id, user_email
