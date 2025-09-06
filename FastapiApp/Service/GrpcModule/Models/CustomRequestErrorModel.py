class RequestKnownError(Exception):
    def __init__(self, message='', code=-2):
        super().__init__(message)  # 👈 调用父类 Exception，便于 traceback 等工具识别
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.code}: {self.message}"


class RequestUnknownError(Exception):
    """未知错误，继承自 RequestKnownError（或你也可以让它直接继承 Exception）"""
    pass  # 不需要重写，直接继承父类行为


class Request412Error(RequestKnownError):
    def __init__(self, message='', code=-412):  # 👈 默认 code 改为 -412 更合理
        super().__init__(message, code)


class Request352Error(RequestKnownError):
    def __init__(self, message='', code=-352):
        super().__init__(message, code)


class RequestProxyResponseError(RequestKnownError):
    def __init__(self, message='', code=-1):
        super().__init__(message, code)