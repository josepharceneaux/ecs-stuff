"""
This module contains our custom pyvalidators, which will be used to valid params based on
docstring with the help of PyContracts.

"""

# TODO-break the doc string so it respects the line limit
from contracts import new_contract


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
    except ValueError:
        # ignore in case of ValueError which means it is already defined
        pass


