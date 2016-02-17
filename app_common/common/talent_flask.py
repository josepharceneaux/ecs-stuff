"""
* TalentFlask is a subclass of Flask which disables strict_slashes rule in Werkzeug routes
"""
from flask import Flask


class TalentFlask(Flask):
    def add_url_rule(self, *args, **kwargs):
        if 'strict_slashes' not in kwargs:
            kwargs['strict_slashes'] = False
        super(TalentFlask, self).add_url_rule(*args, **kwargs)