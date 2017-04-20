from user_service.common.constants import INPUT, PRE_DEFINED
from user_service.common.tests.fake_testing_data_generator import fake

TEST_CUSTOM_FIELDS = [{'name': fake.word(), 'type': INPUT}, {'name': fake.word(), 'type': INPUT},
                      {'name': 'State of Interest', 'type': INPUT},
                      {'name': 'City of Interest', 'type': PRE_DEFINED},
                      {'name': 'Subscription Preference', 'type': PRE_DEFINED}, {'name': 'NUID', 'type': INPUT}]
NUMBER_OF_SAVED_CUSTOM_FIELDS = {INPUT: len([cf for cf in TEST_CUSTOM_FIELDS if cf['type'] == INPUT]),
                                 PRE_DEFINED: len([cf for cf in TEST_CUSTOM_FIELDS if cf['type'] == PRE_DEFINED])}
