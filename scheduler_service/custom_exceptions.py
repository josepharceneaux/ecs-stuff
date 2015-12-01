__author__ = 'saad'


class JobAlreadyPaused:
    def __init__(self, message):
        self.message = message
        self.code = 6053

    def to_dict(self):
        return dict(message=self.message,
                    code=self.code)


class PendingStatus:
    def __init__(self, message):
        self.message = message
        self.code = 6052

    def to_dict(self):
        return dict(message=self.message,
                    code=self.code)


class JobAlreadyRunning:
    def __init__(self, message):
        self.message = message
        self.code = 6054

    def to_dict(self):
        return dict(message=self.message,
                    code=self.code)


class NoJobFound:
    def __init__(self, message):
        self.message = message
        self.code = 6050

    def to_dict(self):
        return dict(message=self.message,
                    code=self.code)
