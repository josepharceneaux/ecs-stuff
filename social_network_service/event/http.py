__author__ = 'zohaib'

import inspect
def http_request():
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    print 'caller name:', calframe[1][3]
    print calframe

