__author__ = 'erikfarmer'
import cStringIO
from bs4.element import ResultSet
from contracts import new_contract
from werkzeug.local import LocalProxy


new_contract('bs4_ResultSet', lambda x: isinstance(x, ResultSet))
new_contract('cStringIO', lambda x: isinstance(x, (cStringIO.InputType, cStringIO.OutputType)))
new_contract('flask_request', lambda x: isinstance(x, LocalProxy))
new_contract('long', lambda x: isinstance(x, long))