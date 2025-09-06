class RequestKnownError(Exception):
    def __init__(self, message='', code=-2):
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.code}: {self.message}"

class RequestUnknownError(Exception):
    def __init__(self, message='', code=-2):
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.code}: {self.message}"


class Request412Error(RequestKnownError):
    def __init__(self, message='', code=-352, ):
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.code}: {self.message}"


class Request352Error(RequestKnownError):
    def __init__(self, message='', code=-352):
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.code}: {self.message}"


class RequestProxyResponseError(RequestKnownError):
    def __init__(self, message='', code=-1):
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.code}: {self.message}"
