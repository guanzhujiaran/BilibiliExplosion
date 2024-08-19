import random

from curl_cffi import requests
from curl_cffi.requests import BrowserType

from grpc获取动态.grpc.bapi.models import LatestVersionBuild


def get_latest_version_builds() -> [LatestVersionBuild]:
    url = "https://app.bilibili.com/x/v2/version?mobi_app=android"
    resp = requests.get(url, impersonate=random.choice(list(BrowserType)).value)
    resp_dict = resp.json()
    return [LatestVersionBuild(**item) for item in resp_dict['data']]


if __name__ == "__main__":
    print([LatestVersionBuild(**x) for x in [
            {
                "build": 8000200,
                "version": "8.0.0"
            },
            {
                "build": 7810200,
                "version": "7.81.0"
            },
            {
                "build": 7800300,
                "version": "7.80.0"
            },
            {
                "build": 7790400,
                "version": "7.79.0"
            },
            {
                "build": 7780300,
                "version": "7.78.0"
            },
            {
                "build": 7770300,
                "version": "7.77.0"
            },
            {
                "build": 7760700,
                "version": "7.76.0"
            },
            {
                "build": 7750300,
                "version": "7.75.0"
            },
            {
                "build": 7740200,
                "version": "7.74.0"
            },
            {
                "build": 7730300,
                "version": "7.73.0"
            },
            {
                "build": 7720200,
                "version": "7.72.0"
            },
            {
                "build": 7710300,
                "version": "7.71.0"
            }
        ]][:10])
