"""
This module contains our custom pyvalidators, which will be used to valid params based on
docstring with the help of PyContracts.

"""
from contracts import new_contract
import cStringIO
from bs4.element import ResultSet
from contracts import new_contract
from werkzeug.local import LocalProxy


def define_custom_contracts():
    """
    This function should be called before calling any method that is using @contract decorator
    This function defined our custom validators which will be used in docstings to be validated by PyContracts library
    """
    try:
        new_contract('long', lambda n: isinstance(n, long))
        new_contract('positive', lambda n: isinstance(n, (int, long, float)) and n > 0)
        new_contract('http_method', lambda method: isinstance(method, basestring) and method.lower() in ['get',
                                                                                                         'post',
                                                                                                         'delete',
                                                                                                         'put',
                                                                                                         'patch'])
        new_contract('bs4_ResultSet', lambda x: isinstance(x, ResultSet))
        new_contract('cStringIO', lambda x: isinstance(x, (cStringIO.InputType, cStringIO.OutputType)))
        new_contract('flask_request', lambda x: isinstance(x, LocalProxy))
    except ValueError:
        # ignore in case of ValueError which means it is already defined
        pass
