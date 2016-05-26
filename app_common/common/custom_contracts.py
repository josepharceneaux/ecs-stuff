from contracts import new_contract


def define_custom_contracts():
    """
    This function should be called before calling any method that is using @contract decorator
    This function defined our custom validators which will be used in docstings to be validated by pycontracts library
    """
    new_contract('long', lambda n: isinstance(n, long))
    new_contract('positive', lambda n: isinstance(n, (int, long, float)) and n > 0)
    new_contract('http_method', lambda method: isinstance(method, basestring) and method.lower() in ['get', 'post', 'delete', 'put', 'patch'])


