import json
import math
import random
import time
import hashlib
import hmac
import binascii
from urllib.parse import urlencode, parse_qs, urlparse

config = {
    'bilibili': {
        'dmImgList': '[{"img_url": "https://i0.hdslb.com/bfs/wbi/7cd084941338484aae1ad9425b84077c.png"}, {"sub_url": "https://i0.hdslb.com/bfs/wbi/4932caff0ff746eab6f01bf08b70ac45.png"}]'
    }
}
def get_time_milli() -> int:
    return int(time.time() * 1000)

def padStringWithZeros(string: str, length: int):
    padding = ''
    if len(string) < length:
        for n in range(length - len(string)):
            padding += '0'
    return padding + string


def dec2HexUpper(e):
    return hex(math.ceil(e))[2:].upper()


def randomHexStr(length):
    string = ''
    for r in range(length):
        string += dec2HexUpper(16 * random.random())
    return padStringWithZeros(string, length)


def lsid():
    ret = ""
    for _ in range(8):
        ret += hex(random.randint(0, 15))[2:].upper()
    ret = f"{ret}_{hex(get_time_milli())[2:].upper()}"
    return ret


def _uuid():
    e = randomHexStr(8)
    t = randomHexStr(4)
    r = randomHexStr(4)
    n = randomHexStr(4)
    o = randomHexStr(12)
    i = int(time.time() * 1000)
    return e + '-' + t + '-' + r + '-' + n + '-' + o + padStringWithZeros(str((i % 100000)), 5) + 'infoc'


def shiftCharByOne(s: str):
    shifted_str = ''
    for char in s:
        shifted_str += chr(ord(char) - 1)
    return shifted_str


def hexsign(e):
    n = 'YhxToH[2q'
    key = shiftCharByOne(n).encode('utf-8')
    message = 'ts' + e
    hashed = hmac.new(key, message.encode('utf-8'), hashlib.sha256)
    o = binascii.hexlify(hashed.digest()).decode('utf-8')
    return o


def addWbiVerifyInfo(params, wbiVerifyString) -> str:
    parsed_params = parse_qs(params)
    sorted_params = sorted([(key, value[0]) for key, value in parsed_params.items()])
    sorted_query_string = urlencode(sorted_params, doseq=True)

    wts = round(time.time())
    verify_param = f"{sorted_query_string}&wts={wts}"
    w_rid = hashlib.md5((verify_param + wbiVerifyString).encode('utf-8')).hexdigest()

    result_params = f"{params}&w_rid={w_rid}&wts={wts}"
    return result_params


def generateGaussianInteger(mean, std):
    _2PI = math.pi * 2
    u1 = random.random()
    u2 = random.random()

    z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(_2PI * u2)

    return round(z0 * std + mean)


def getDmImgList():
    if 'bilibili' in config and 'dmImgList' in config['bilibili']:
        dm_img_list = json.loads(config['bilibili']['dmImgList'])
        return json.dumps([dm_img_list[random.randint(0, len(dm_img_list) - 1)]])

    x = max(generateGaussianInteger(650, 5), 0)
    y = max(generateGaussianInteger(400, 5), 0)
    path = [
        {
            'x': 3 * x + 2 * y,
            'y': 4 * x - 5 * y,
            'z': 0,
            'timestamp': max(generateGaussianInteger(30, 5), 0),
            'type': 0,
        },
    ]
    return json.dumps(path)
