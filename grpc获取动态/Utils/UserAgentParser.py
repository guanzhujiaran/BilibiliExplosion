import random
import re
import uuid

ANDROID_VERSIONS = {
    '1.0': 1, '1.1': 2, '1.5': 3, '1.6': 4, '2.0': 5, '2.0.1': 6, '2.1': 7, '2.2': 8, '2.3': 9, '2.3.3': 10,
    '3.0': 11, '3.1': 12, '3.2': 13, '4.0': 14, '4.0.3': 15, '4.0.4': 15, '4.1': 16, '4.1.1': 16, '4.2': 17,
    '4.3': 18, '4.4': 19, '4.4W': 20, '5.0': 21, '5.1': 22, '6.0': 23, '6': 23, '7.0': 24, '7': 24, '7.1': 25,
    '8.0': 26, '8': 26,
    '8.1': 27, '9.0': 28, '9': 28, '10.0': 29, '10': 29, '11.0': 30, '11': 30, '12.0': 31, '12': 31, '12.1': 32,
    '13.0': 33,
    '13': 33
}


class UserAgentParser:
    def __init__(self, user_agent, is_mobile=False, fetch_dest='empty', fetch_mode='cors', fetch_site='same-site'):
        self.user_agent = user_agent
        self.is_mobile = is_mobile
        self.fetch_dest = fetch_dest
        self.fetch_mode = fetch_mode
        self.fetch_site = fetch_site
        self.sec_ch_ua = self.parse_user_agent()
        self.sec_ch_ua_mobile = self.parse_sec_ch_ua_mobile()
        self.sec_ch_ua_platform = self.parse_sec_ch_ua_platform()

    def parse_user_agent(self):
        # 解析User-Agent字符串
        if 'Chrome' in self.user_agent:
            match = re.search(r'Chrome/(\d+)', self.user_agent)
            if match:
                chrome_version = match.group(1)
                return f'"Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}", "Not;A=Brand";v="99"'

        if 'Edg' in self.user_agent:
            match = re.search(r'Edg/(\d+)', self.user_agent)
            if match:
                edge_version = match.group(1)
                return f'"Chromium";v="{edge_version}", "Microsoft Edge";v="{edge_version}", "Not;A=Brand";v="24"'

        if 'Firefox' in self.user_agent:
            match = re.search(r'Firefox/(\d+\.\d+)', self.user_agent)
            if match:
                firefox_version = match.group(1)
                return f'"Not;A=Brand";v="99", "Mozilla Firefox";v="{firefox_version}"'

        if 'Safari' in self.user_agent and 'Version' in self.user_agent:
            match = re.search(r'Version/(\d+\.\d+)', self.user_agent)
            if match:
                safari_version = match.group(1)
                return f'"Not;A=Brand";v="99", "Safari";v="{safari_version}"'

        # 如果没有匹配到已知的浏览器，返回默认值
        return '"Unknown";v="0"'

    def parse_sec_ch_ua_mobile(self):
        # 根据is_mobile属性设置sec-ch-ua-mobile
        return '?1' if self.is_mobile else '?0'

    def parse_sec_ch_ua_platform(self):
        # 解析平台信息
        if 'Windows' in self.user_agent:
            return '"Windows"'
        elif 'Mac' in self.user_agent:
            return '"macOS"'
        elif 'Linux' in self.user_agent:
            return '"Linux"'
        elif 'Android' in self.user_agent:
            return '"Android"'
        elif 'iOS' in self.user_agent:
            return '"iOS"'
        else:
            return '"Unknown"'

    def get_headers_dict(self, *args) -> dict:
        origin_headers = {
            'user-agent': self.user_agent,
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'referer': '',
            'origin': '',
            'cookie': '',
            'priority': 'u=4',
            'sec-ch-ua': self.sec_ch_ua,
            'sec-ch-ua-mobile': self.sec_ch_ua_mobile,
            'sec-ch-ua-platform': self.sec_ch_ua_platform,
            'sec-fetch-dest': self.fetch_dest,
            'sec-fetch-mode': self.fetch_mode,
            'sec-fetch-site': self.fetch_site,
        }
        origin_headers.update(*args)
        filtered_headers_dict = {key: value for key, value in origin_headers.items() if value}
        return filtered_headers_dict

    @staticmethod
    def parse_h5_ua(dalvik_ua, buvid) -> str:
        def get_sdk_int(_android_version):
            # 根据Android版本获取对应的SDK Int
            for _version, _sdk_int in ANDROID_VERSIONS.items():
                if _android_version.startswith(_version):
                    return _sdk_int
            return None

        def generate_random_versions():
            # 生成合理的WebKit、Chrome和Safari版本号
            webkit_version = "537.36"  # WebKit版本通常固定为537.36
            chrome_major = random.randint(70, 100)  # 选择一个合理的Chrome主版本号范围
            chrome_minor = random.randint(0, 99)
            chrome_patch = random.randint(0, 9999)
            chrome_version = f"{chrome_major}.0.{chrome_minor}.{chrome_patch}"

            safari_version = "537.36"  # Safari版本通常与WebKit版本相同

            return webkit_version, chrome_version, safari_version

        if 'Mozilla/5.0' in dalvik_ua:  # 本来就是Mozilla的ua就直接返回
            return dalvik_ua
        device_info_match = re.search(r'\(([^)]+)\)', dalvik_ua)
        if not device_info_match:
            return dalvik_ua

        device_info = device_info_match.group(1)
        # 提取其他参数
        app_version_match = re.search(r'(?<=\))\s*(\d+\.\d+\.\d+)', dalvik_ua)
        if not app_version_match:
            app_version = "8.13.0"
        else:
            app_version = app_version_match.group(1)
        build_number = re.search(r'build/(\d+)', dalvik_ua).group(1) if 'build/' in dalvik_ua else '8130300'
        channel = re.search(r'channel/(\w+)', dalvik_ua).group(1) if 'channel/' in dalvik_ua else 'master'

        # 提取Android版本
        android_version_match = re.search(r'Android (\d+(\.\d+)?(\.\d+)?)', dalvik_ua)
        if not android_version_match:
            android_version = '9'
        else:
            android_version = android_version_match.group(1)
        sdk_int = get_sdk_int(android_version)

        # 提取设备型号
        model_match = re.search(r'Android \d+(\.\d+)?(\.\d+)?; ([^ ;]+)', device_info)
        if not model_match:
            model = '23113RKC6C'
        else:
            model = model_match.group(3)
        # 随机会话ID
        session_id = uuid.uuid4().hex[0:8]

        # 生成随机版本号
        webkit_version, chrome_version, safari_version = generate_random_versions()
        # 构建Mozilla/5.0格式的UA字符串
        mozilla_ua = (
            f"Mozilla/5.0 ({device_info}) "
            f"AppleWebKit/{webkit_version} (KHTML, like Gecko) Version/4.0 Chrome/{chrome_version} Mobile Safari/{safari_version} "
            f"os/android model/{model} build/{build_number} osVer/{android_version} sdkInt/{sdk_int} network/2 BiliApp/{build_number} "
            f"mobi_app/android channel/{channel} Buvid/{buvid} sessionID/{session_id} innerVer/{build_number} c_locale/zh_CN s_locale/zh_CN "
            f"disable_rcmd/0 themeId/1 sh/24 {app_version} os/android model/{model} mobi_app/android build/{build_number} "
            f"channel/{channel} innerVer/{build_number} osVer/{android_version} network/2"
        )

        return mozilla_ua


if __name__ == "__main__":
    # 使用示例
    user_agent = 'Dalvik/2.1.0 (Linux; U; Android 5.1; Impress Style Build/LMY47I) 8.2.0 os/android model/Impress Style mobi_app/android build/8020300 channel/360 innerVer/8020300 osVer/5.1 network/2'
    ua_parser = UserAgentParser.parse_h5_ua(user_agent, 114514)
    print(ua_parser)
