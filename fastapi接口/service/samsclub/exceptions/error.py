class StopError(Exception):
    """停止错误"""

    def __init__(self, msg: str):
        self.msg = msg if msg else "未知"
        super().__init__(self.msg)

    def __str__(self):
        return f'退出！原因：{self.msg}'


class UnknownError(Exception):
    """未知错误"""

    def __init__(self, msg: str):
        self.msg = msg if msg else "未知"
        super().__init__(self.msg)

    def __str__(self):
        return f'未知错误！原因：{self.msg}'

class AUTH_FAIL(StopError):
    """授权失败错误 也就是登录状态掉了"""

    def __init__(self, msg: str):
        self.msg = msg if msg else "未知"
        super().__init__(self.msg)
    def __str__(self):
        return f'授权失败！原因：{self.msg}'
