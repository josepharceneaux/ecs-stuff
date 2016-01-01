from flask.ext.restful import Api


class TalentApi(Api):
    """
    This class extends error handling functionality for flask.restful.Api class.
    flask.restful.Api does not provide a good way of handling custom exceptions and
    returning dynamic response.

    In flask.restful.Api.handle_error(e) method, it just says "Internal Server Error" for
    our custom exceptions so we are overriding this method and now it raises again out custom
    exceptions which will be caught by error handlers in error_handling.py module.
     and if it is some other exception then actual method will handle it.
    """
    def handle_error(self, e):
        # if it is our custom exception or its subclass instance then raise it
        # so it error_handlers for app can catch this error and can send proper response
        # in required format

        # check whether this exception is some child class of TalentError base class.
        # if isinstance(e, TalentError): # isinstance does not work well due to different import styles
        bases = [cls.__name__ for cls in e.__class__.__mro__]
        if 'TalentError' in bases:
            raise
        else:
            # if it is not a custom exception then let the Api class handle it.
            return super(TalentApi, self).handle_error(e)
