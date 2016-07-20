__author__ = 'erikfarmer'
import cStringIO
from bs4.element import ResultSet
from contracts import new_contract
from flask import request
from werkzeug.local import LocalProxy


new_contract('cStringIO_StringIO', lambda x: isinstance(x, (cStringIO.InputType, cStringIO.OutputType)))
new_contract('bs4_ResultSet', lambda x: isinstance(x, ResultSet))
new_contract('flask_request', lambda x: isinstance(x, LocalProxy))