"""
This module will implement Timeout class which will raise an exception whenever a function exceeds given timestamp
"""
import signal


class TimeoutException(Exception):
    pass


class Timeout:

    def __init__(self, seconds=1, error_message='Function has timed out'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutException(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)

