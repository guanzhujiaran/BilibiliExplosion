import json


class ReserveRelationInfoResponseError(Exception):
    def __init__(self, message='', code=-1):
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.code}: {self.message}"


def check_reserve_relation_info(resp: dict, *, ids: int | str) -> bool:
    available_code_set = {0, 9999}
    if resp.get('code') not in available_code_set:
        raise ReserveRelationInfoResponseError(message=f'响应代码错误！\n{resp}', code=resp.get('code'))
    if resp.get('code') == 0 and resp.get('data'):
        if str(ids) not in json.dumps(resp):
            raise ReserveRelationInfoResponseError(message=f'响应数据内容错误！ids={ids}\n{resp}', code=resp.get('code'))
    return True
