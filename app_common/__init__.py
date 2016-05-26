__author__ = 'jitesh'
from common.custom_contracts import define_custom_contracts

try:
    define_custom_contracts()
except ValueError:
    # ignore in case of ValueError, it is due to calling this function twice
    pass
