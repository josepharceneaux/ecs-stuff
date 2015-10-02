from flask import Flask
from flask_restful import Resource, Api
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
api = Api(app)

# Session = sessionmaker()
#
#
# class CandidateAPI(Resource):
#     def get(self, candidate_id):
#
#         return Candidate
#
# api.add_resource(Candidate, '/api/candidates')
#
#
# if __name__ == '__main__':
#     app.run(debug=True)


