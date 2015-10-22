from candidate_service.app import app
from candidate_service.app.api.v1_candidates import CandidateResource


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004, use_reloader=True, debug=False)

