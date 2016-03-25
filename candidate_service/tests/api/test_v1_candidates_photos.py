# Candidate Service app instance
from candidate_service.candidate_app import app

# Conftest
from candidate_service.common.tests.conftest import *

# Helper functions
from helpers import AddUserRoles
from candidate_service.common.utils.test_utils import send_request, response_info
from candidate_service.common.routes import CandidateApiUrl

# Candidate sample data
from candidate_sample_data import generate_single_candidate_data

# Custom error
from candidate_service.custom_error_codes import CandidateCustomErrors as custom_error


class TestCandidatePhoto(object):
    def test_create_candidate_photo(self, access_token_first, user_first, talent_pool):
        """
        Test: Create candidate photo
        Expect: 201
        """
        # Create Candidate
        AddUserRoles.add_and_get(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Add Photo to candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = {'photos': [
            {'image_url': 'www.foo.com', 'added_time': datetime.isoformat(datetime.utcnow())},
            {'image_url': 'www.goo.com'}
        ]}
        create_photo = send_request('post', CandidateApiUrl.PHOTOS % candidate_id, access_token_first, data)
        # create_photo = request_to_candidate_photos_resource(token=access_token_first,
        #                                                     request='post', candidate_id=candidate_id,
        #                                                     data=data)
        print response_info(create_photo)
        assert create_photo.status_code == 204

        # Retrieve candidate's photo
        get_resp = send_request('get', CandidateApiUrl.CANDIDATE % candidate_id, access_token_first)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_photos']) == 2

    def test_create_duplicate_photos(self, access_token_first, user_first, talent_pool):
        """
        Test: Attempt to create two photos with the same url for the same candidate in the same domain
        Expect: 204, but duplicate image_url should not be inserted into the db
        """
        # Create candidate
        AddUserRoles.add_and_get(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Add Photo to candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = {'photos': [{'image_url': 'www.foo.com'}, {'image_url': 'www.foo.com'}]}
        create_photo = request_to_candidate_photos_resource(access_token_first, 'post',
                                                            candidate_id=candidate_id,
                                                            data=data)
        assert create_photo.status_code == 204
        print response_info(create_photo)

        # Retrieve candidate's photo
        get_resp = request_to_candidate_photos_resource(access_token_first, 'get', candidate_id)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert len(get_resp.json()['candidate_photos']) == 1


class TestCandidatePhotoEdit(object):
    def test_update_candidate_photo(self, access_token_first, user_first, talent_pool):
        # Create candidate
        AddUserRoles.add_get_edit(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = request_to_candidates_resource(access_token_first, 'post', data=data)
        print response_info(create_resp)

        # Add candidate photo
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = {'photos': [
            {'image_url': fake.url()}, {'image_url': fake.url()}, {'image_url': fake.url()}
        ]}
        create_photo = request_to_candidate_photos_resource(access_token_first, 'post',
                                                            candidate_id=candidate_id,
                                                            data=data)
        print response_info(create_photo)

        # Retrieve candidate's photos
        get_resp = request_to_candidate_photos_resource(access_token_first, 'get', candidate_id)
        print response_info(get_resp)
        candidate_photos = get_resp.json()['candidate_photos']
        assert candidate_photos[-1]['is_default'] == False

        # Update candidate's photo
        last_photo_id = candidate_photos[-1]['id']
        data = {'photos': [{'id': last_photo_id, 'is_default': True}]}
        update_resp = request_to_candidate_photos_resource(access_token_first, 'patch', candidate_id, data=data)
        print response_info(update_resp)

        # Retrieve candidate photo again and check new is_default value
        get_resp = request_to_candidate_photos_resource(access_token_first, 'get', candidate_id,
                                                        last_photo_id)
        print response_info(get_resp)
        assert get_resp.status_code == 200
        assert get_resp.json()['candidate_photo']['is_default'] == True


class TestCandidatePhotoDelete(object):
    def test_delete_candidate_photos(self, access_token_first, user_first, talent_pool):
        # Create candidate
        AddUserRoles.all_roles(user_first)
        data = generate_single_candidate_data([talent_pool.id])
        create_resp = send_request('post', CandidateApiUrl.CANDIDATES, access_token_first, data)
        print response_info(create_resp)
        assert create_resp.status_code == 201

        # Add Photo to candidate
        candidate_id = create_resp.json()['candidates'][0]['id']
        data = {'photos': [
            {'image_url': fake.url()}, {'image_url': fake.url()}, {'image_url': fake.url()}
        ]}
        create_photo = request_to_candidate_photos_resource(access_token_first, 'post',
                                                            candidate_id=candidate_id,
                                                            data=data)
        assert create_photo.status_code == 204
        print response_info(create_photo)

        # Retrieve candidate's photos
        get_resp = request_to_candidate_photos_resource(access_token_first, 'get', candidate_id)
        print response_info(get_resp)
        candidate_photos = get_resp.json()['candidate_photos']
        assert len(candidate_photos) == 3

        # Delete one of candidate's photos
        del_resp = request_to_candidate_photos_resource(access_token_first, 'delete', candidate_id,
                                                        candidate_photos[0]['id'])
        print response_info(del_resp)
        # Retrieve candidate's photo
        get_resp = request_to_candidate_photos_resource(access_token_first, 'get', candidate_id)
        assert len(get_resp.json()['candidate_photos']) == 2

        # Delete all of candidate's photos
        del_all_resp = request_to_candidate_photos_resource(access_token_first, 'delete', candidate_id)
        print response_info(del_all_resp)
        # Retrieve candidate's photo
        get_resp = request_to_candidate_photos_resource(access_token_first, 'get', candidate_id)
        print response_info(get_resp)
        assert len(get_resp.json()['candidate_photos']) == 0