import asyncio
import json
from hashlib import md5
import httpx

from fastapi接口.log.base_log import sams_club_logger
from fastapi接口.models.v1.samsclub.samsclub_model import SamsClubEncryptModel, SamsClubGetDoEncryptReqModel
from CONFIG import CONFIG


def get_st(samsClubEncryptModel: SamsClubEncryptModel):
    """

    :param samsClubEncryptModel: 这个model需要先把里面的内容填充好再传进来
    :return:
    """
    device_id_str = samsClubEncryptModel.device_id_str
    do_encrypt_result_str = samsClubEncryptModel.do_encrypt_result_str
    version_str = samsClubEncryptModel.version_str

    return md5(
        f"{do_encrypt_result_str}{device_id_str}android{version_str}B6@N7#M8$Q9%W1^E".encode("utf-8")).hexdigest()


async def get_do_encrypt_result_str(samsClubGetDoEncryptReqModel: SamsClubGetDoEncryptReqModel):
    url = CONFIG.unidbg_addr + '/api/app/samsclub/doEncrypt'
    body = samsClubGetDoEncryptReqModel.model_dump()
    async with httpx.AsyncClient() as __asc:
        resp = await __asc.post(url, json=body,
                                headers={
                                    "Content-Type": "application/json",
                                })
    resp.raise_for_status()
    if len(resp.text) == 32:
        sams_club_logger.debug(f"解密成功！{resp.text}")
        return resp.text
    else:
        raise ValueError(f"解密失败！{resp.text}")


async def update_do_encrypt_key(siv, ssk, srd):
    url = CONFIG.unidbg_addr + '/api/app/samsclub/updateKey'
    body = {
        "siv": siv,
        "ssk": ssk,
        "srd": srd
    }
    async with httpx.AsyncClient() as __asc:
        resp = await __asc.post(url,
                                json=body,
                                headers={
                                    "Content-Type": "application/json",
                                })
    resp.raise_for_status()


if __name__ == '__main__':
    print(asyncio.run(get_do_encrypt_result_str(
        SamsClubGetDoEncryptReqModel(
            timestampStr="1747819632376",
            bodyStr=json.dumps(
                {
                    "deviceType": 1,
                    "pushOpen": "1",
                    "token": "042b2013d15fed9dc0932b7f7fea12a8c854",
                    "uid": "1818144697779"
                }, ensure_ascii=False, separators=(',', ':')
            ),
            uuidStr="e44cc0cf0c2b461a8a659d529d913e5d",
            tokenStr="740d926b981716f4212cb48a4fb7591f9f984d92ee660d5179580a5d95729f81129e1b87cc8bd60f8f9d1a3f88fb7dfa2691e4d19f66631d"
        )
    ))
    )
