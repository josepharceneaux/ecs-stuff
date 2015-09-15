from flask import Flask
from flask_restful import Resource, Api, reqparse, abort

app = Flask(__name__)
api = Api(app=app)

# class DomainAPI():
#
#     def get(self, domain_id=None):
#         if domain_id is None:
#             all_domains = Domain.query.all()
#
#     def post(self, *args, **kwargs):
#
#         # Logged in user must be a getTalent admin (Customer Manager)
#
#         print args
#         print kwargs
#
#         return {'domain': {'id': "domain id of the newly created domain"}}
#
# api.add_resource(DomainAPI, '/api/domains')