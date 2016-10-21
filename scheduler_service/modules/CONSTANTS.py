"""
CONSTANTS file containing global constants used across scheduler service and tests
"""

REQUEST_COUNTER = 'count_%s_request'
SCHEDULER_PERIODIC_REQUIRED_PARAMETERS = ['frequency', 'task_type', 'start_datetime', 'end_datetime', 'url']
SCHEDULER_ONE_TIME_REQUIRED_PARAMETERS = ['run_datetime', 'url']
