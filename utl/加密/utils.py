import random
import time

config = {
    'bilibili': {
        'dmImgList': '[{"img_url": "https://i0.hdslb.com/bfs/wbi/7cd084941338484aae1ad9425b84077c.png"}, {"sub_url": "https://i0.hdslb.com/bfs/wbi/4932caff0ff746eab6f01bf08b70ac45.png"}]'
    }
}


def get_time_milli() -> int:
    return int(time.time() * 1000)


def lsid():
    ret = ""
    for _ in range(8):
        ret += hex(random.randint(0, 15))[2:].upper()
    ret = f"{ret}_{hex(get_time_milli())[2:].upper()}"
    return ret
