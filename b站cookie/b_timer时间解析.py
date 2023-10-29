import json
import time
from urllib import parse
import numpy
'''
短时间内参加许多的天选容易被标记b_timer
'''
import Bilibili_methods.all_methods

bapi = Bilibili_methods.all_methods.methods()


class b_timer_resolution:
    def url_decode(self, s):
        t = s.replace('%22', '"').replace('%23', '#').replace('%24', '$').replace('%25', '%').replace('%26',
                                                                                                      '&').replace(
            '%27', '\'').replace('%28', '(').replace('%29', ')').replace('%2A', '*').replace('%2B', '+').replace('%2C',
                                                                                                                 ',').replace(
            '%2D', '-').replace('%2E', '.').replace('%2F', '/').replace('%3A', ':').replace('%3B', ';').replace('%3C',
                                                                                                                '<').replace(
            '%3D', '=').replace('%3E', '>').replace('%3F', '?').replace('%5B', '[').replace('%5C', '\\').replace('%5D',
                                                                                                                ']').replace(
            '%5E', '^').replace('%5F', '_').replace('%60', '`').replace('%7B', '{').replace('%7C', '|').replace('%7D',
                                                                                                                '}').replace(
            '%7E', '~')
        return t

    def get_b_timer_from_cookie(self, cookie):
        c_s = cookie.split(';')
        for i in c_s:
            if i != '':
                k = i.strip().split('=')[0].strip()
                v = i.strip().split('=')[1].strip()
                if k == "b_timer":
                    return v

    def rule_explain(self, violation_code):
        if '0.0' in violation_code:
            return ('预约抽奖详情页面',
                    'https://www.bilibili.com/h5/lottery/result?business_id=724206&business_type=10&lottery_id=97032')
        if '333.52' in violation_code:
            return ('支付页面', 'https://big.bilibili.com/pc/payVip/?appId=18&appSubId=')
        if '448.588' in violation_code:
            return ('社群每日签到活动', 'https://mall.bilibili.com/act/aicms/hdkgr4wQok.html')
        if '333.788' in violation_code:
            return ('直播页面 or 普通视频播放页（大概率影响天选中奖）')
        if '444.41' in violation_code:
            return ('动态主页', 'https://t.bilibili.com')
        if '333.1007' in violation_code:
            return ('主站主页', 'https://www.bilibili.com/')
        if '444.42' in violation_code:
            return ('动态详情页')
        if '777.5' in violation_code:
            return ('检查b_timer')
        if '666.4' in violation_code:
            return ('番剧页面')
        if '666.5' in violation_code:
            return ('国创页面')
        if '666.8' in violation_code:
            return ('电视剧页面')
        if '666.32' in violation_code:
            return ('综艺页面')
        if '666.9' in violation_code:
            return ('纪录片页面')
        if '333.1073' in violation_code:
            return ('动画游戏鬼畜音乐舞蹈影视娱乐知识科技资讯美食生活等主页分区页面')
        if '333.909' in violation_code:
            return ('频道页面')
        if '666.25' in violation_code:
            return ('番剧观看页面')
        if '333.880' in violation_code:
            return ('观看历史页面')
        if '333.999' in violation_code:
            return ('空间主页（包括自己的）', 'https://space.bilibili.com/1328260/')
        if '333.3' in violation_code:
            return ('个人中心页面', 'https://account.bilibili.com/account/home')
        if '333.979' in violation_code:
            return ('我的钱包页面', 'https://pay.bilibili.com/pay-v2-web/bcoin_index')
        if '333.33' in violation_code:
            return ('实名认证页面', 'https://account.bilibili.com/account/realname/identify')
        if '333.1111' in violation_code:
            return ('赛事中心主页 or 其底下分区', 'https://www.bilibili.com/match/home/')

        if '555.51' in violation_code:
            return ('游戏中心大会员福利页面', 'https://b-gift.biligame.com/')
        if '555.44' in violation_code:
            return ('游戏中心我的礼包页面', 'https://b-gift.biligame.com/list_my.html')
        if '555.117' in violation_code:
            return ('游戏中心wiki首', 'https://wiki.biligame.com/wiki/%E9%A6%96%E9%A1%B5')
        if '555.120' in violation_code:
            return ('游戏中心主页 or 新版游戏中心试用意见反馈页面', 'https://game.bilibili.com/platform/')
        if '555.121' in violation_code:
            return ('游戏中心发现页', 'https://game.bilibili.com/platform/discover')
        if '555.122' in violation_code:
            return ('游戏中心热度榜', 'https://game.bilibili.com/platform/ranks/expectation')
        if '555.123' in violation_code:
            return ('游戏中心预约帮', 'https://game.bilibili.com/platform/ranks/expectation')
        if '555.124' in violation_code:
            return ('游戏中心口碑榜', 'https://game.bilibili.com/platform/ranks/reputation')
        if '555.125' in violation_code:
            return ('游戏中心B指数榜', 'https://game.bilibili.com/platform/ranks/bindex')
        if '555.126' in violation_code:
            return ('游戏中心开测表', 'https://game.bilibili.com/platform/ranks/testing')
        if '555.43' in violation_code:
            return ('游戏客服专区', 'https://game.bilibili.com/kf/')
        if '555.45' in violation_code:
            return ('哔哩哔哩游戏详情页', 'https://www.biligame.com/detail/?id= #id为游戏id')
        if '555.128' in violation_code:
            return ('哔哩哔哩个人空间页', 'https://game.bilibili.com/platform/mine/home')
        if '888.68171' in violation_code:
            return ('周年庆活动页面', 'https://www.bilibili.com/anniversary-13')
        if '333.934' in violation_code:
            return ('热门排行榜', 'https://www.bilibili.com/v/popular/all')
        if '111.1' in violation_code:
            return ('626会员购星球', 'https://mall.bilibili.com/zq/starpartying-2022626-1/?noTitleBar=1')
        if '333.337' in violation_code:
            return ('搜索页面','https://search.bilibili.com/all')
        if '555.77' in violation_code:
            return ('哔哩哔哩游戏周年页面','https://game.bilibili.com/HAPPYday/2022/h5/')


    def b_timer_res(self, b_timer_str):
        v = self.url_decode(b_timer_str)
        d = eval(v)
        vi = d['ffp']
        print('当前风控数量：{}'.format(len(vi)))
        for k, v in vi.items():
            print(k, self.rule_explain(k), bapi.timeshift(int(str(v), 16) / 1000))


if __name__ == '__main__':
    b = b_timer_resolution()
    # 斯卡蒂：ck = "_uuid=4610455EE-A23B-6426-367B-52A6898C6B1706899infoc; buvid4=0DE48A73-B1FF-C9DB-C60B-8014D47552B507794-022052800-TDIcPGmL6+BfjziClj/3KQ%3D%3D; buvid3=AF2477C2-272A-BF16-B6F1-95FDCE2BA28C07794infoc; b_nut=1653669307; buvid_fp_plain=undefined; hit-dyn-v2=1; CURRENT_BLACKGAP=0; blackside_state=0; rpdid=|(J|)kmuY|l)0J'uYlJYYml|R; nostalgia_conf=-1; deviceFingerprint=aa11154b34228952c02be1fc03600659; CURRENT_QUALITY=116; go_old_video=-1; dy_spec_agreed=1; i-wanna-go-back=-1; b_ut=5; bp_video_offset_1905702375=673421258384212000; msource=game_magic; kfcSource=game_magic; c=V6tPWQlv-1655632419834-b235eb38cd35f1428742968; canvasFp=13edc6916b4988e7a6999eb666bc8004; webglFp=1d912dbcf614fed8d8af994b638de040; screenInfo=1920*1080*24; feSign=4a555eb21c171ba3da203c00c8353f33; payParams=%7B%22customerId%22%3A10002%2C%22serviceType%22%3A14%2C%22orderId%22%3A%22299393704%22%2C%22orderCreateTime%22%3A1655632417000%2C%22orderExpire%22%3A180%2C%22feeType%22%3A%22CNY%22%2C%22payAmount%22%3A256%2C%22originalAmount%22%3A1500%2C%22deviceType%22%3A2%2C%22deviceInfo%22%3A%22web%22%2C%22notifyUrl%22%3A%22http%3A//mall.bilibili.co/mall-trade/order/pay/callback%22%2C%22productId%22%3A%2210086888%22%2C%22productUrl%22%3A%22https%3A//mall.bilibili.com/neul/index.html%3Fpage%3Dbox_detail%26noTitleBar%3D1%23itemsId%3D10086888-4005467681936487%22%2C%22showTitle%22%3A%22%u4EBA%u6C14%u624B%u529E%u5408%u96C6-2%20SSR%u9B54%u529B%u8D4F%22%2C%22showContent%22%3A%22%u4EBA%u6C14%u624B%u529E%u5408%u96C6-2%20SSR%u9B54%u529B%u8D4F%22%2C%22createIp%22%3A%22183.193.145.67%22%2C%22createUa%22%3A%22Mozilla/5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit/537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome/102.0.0.0%20Safari/537.36%22%2C%22returnUrl%22%3A%22https%3A//mall.bilibili.com/neul/index.html%3Fpage%3Dbox_detail%26noTitleBar%3D1%23itemsId%3D10086888-4005467681936487%22%2C%22failUrl%22%3A%22http%3A//mall.bilibili.com/orderlist.html%3Fstatus%3D0%22%2C%22extData%22%3A%22%7B%5C%22orderId%5C%22%3A4005467681936487%7D%22%2C%22traceId%22%3A%221655632419064%22%2C%22timestamp%22%3A1655632419064%2C%22version%22%3A%221.0%22%2C%22signType%22%3A%22MD5%22%2C%22sign%22%3A%223ffbeb0c92537f21dc3802e8c8e40830%22%2C%22defaultChoose%22%3A%22alipay%22%2C%22uid%22%3A1905702375%2C%22grayChannel%22%3A1%7D; _fmdata=UFAeswMPivIGgjTtQ8S%2Bfr3BEW9d21rDFYZ28UhZy3vqNE1aNCBTkEtX2SW%2BDcd34pfGFcCcnNU%2Bld%2BLQzXiSS%2BedqNLi%2BZ%2BZyde5Mwk3xI%3D; _xid=jzyQxIBe%2F0%2BXj124t68PNN8qocDvkfc%2BJ1J9QWumLou%2FdGxyW1w8DIf%2FE2RvAQjLnH9%2FsfLP3j%2BWlgv0nH3umw%3D%3D; SESSDATA=e36fa2fd%2C1671278801%2C4640e%2A61; bili_jct=93c44ed7667063934b8c041eea7a337c; DedeUserID=1905702375; DedeUserID__ckMd5=e66cfea7736b82c2; sid=j66ygygt; buvid_fp=a76642a97375e11bf59547c07f681818; from=cms_658_MilfxYgRyTZE_; i-wanna-go-feeds=2; bsource=share_source_copy_link; is-2022-channel=1; fingerprint=0ed207bb341c1a83f589729bcb570c9e; fingerprint3=33b710a19f96c64ff2f14cb4d05a8028; innersign=0; kfcFrom=cms_1570_MNVD3cfFISqf_; LIVE_BUVID=AUTO8016558171659806; CURRENT_FNVAL=80; PVID=1; b_timer=%7B%22ffp%22%3A%7B%22555.43.fp.risk_AF2477C2%22%3A%2218182304F8C%22%2C%22333.794.fp.risk_AF2477C2%22%3A%221818232DBB5%22%2C%22777.5.0.0.fp.risk_AF2477C2%22%3A%221818663FCF2%22%2C%22333.979.fp.risk_AF2477C2%22%3A%2218182332760%22%2C%22333.999.fp.risk_AF2477C2%22%3A%221818663D961%22%2C%22888.68171.fp.risk_AF2477C2%22%3A%221818235BF82%22%2C%220.0.fp.risk_AF2477C2%22%3A%221818235C338%22%2C%22333.937.fp.risk_AF2477C2%22%3A%2218182376743%22%2C%22444.41.fp.risk_AF2477C2%22%3A%221818663EA89%22%2C%22333.1007.fp.risk_AF2477C2%22%3A%221818663EA7D%22%2C%22444.42.fp.risk_AF2477C2%22%3A%221818663F261%22%2C%22448.1549.fp.risk_AF2477C2%22%3A%22181866405E7%22%2C%22444.8.fp.risk_AF2477C2%22%3A%2218186640651%22%2C%22448.1552.fp.risk_AF2477C2%22%3A%2218186640DD5%22%2C%22448.1601.fp.risk_AF2477C2%22%3A%22181866411A7%22%2C%22888.453.fp.risk_AF2477C2%22%3A%22181866411B8%22%2C%22448.1505.fp.risk_AF2477C2%22%3A%2218186641585%22%2C%22448.1555.fp.risk_AF2477C2%22%3A%2218186642134%22%2C%22333.337.fp.risk_AF2477C2%22%3A%221818685FC62%22%2C%22555.120.fp.risk_AF2477C2%22%3A%221818686C31C%22%7D%7D; b_lsid=F482D49C_18186B657F0"
    ck="l=v; _uuid=9AF971AD-F529-E775-D359-58CAC35648AD16177infoc; buvid3=5851F775-49B6-81D2-3820-D5C32C9780EC16730infoc; b_nut=1659608916; buvid_fp_plain=undefined; SESSDATA=109a6bf1%2C1675160936%2Ca1b62%2A81; bili_jct=4d823be468fbf1f3e1ffebfe93ca8731; DedeUserID=1905702375; DedeUserID__ckMd5=e66cfea7736b82c2; sid=8gtz5kkc; hit-dyn-v2=1; nostalgia_conf=-1; i-wanna-go-back=-1; b_ut=5; CURRENT_BLACKGAP=0; rpdid=|(J|)kmuYuJY0J'uYlmYuR~)u; deviceFingerprint=a5fee0693c76438e67cb7f89c38867e2; buvid4=F1EE141A-CB6E-FC1B-FA10-2E9B5040A32516730-022080418-TDIcPGmL6%2BCYGUTm56sAMg%3D%3D; dy_spec_agreed=1; is-2022-channel=1; b_timer=%7B%22ffp%22%3A%7B%22333.171.fp.risk_5851F775%22%3A%22182B0810D27%22%2C%22888.2421.fp.risk_5851F775%22%3A%22182C61CC2B6%22%2C%22777.5.0.0.fp.risk_5851F775%22%3A%22182C61CC358%22%2C%22333.30.fp.risk_5851F775%22%3A%22182B75CCC0C%22%2C%22444.42.fp.risk_5851F775%22%3A%22182D0E58E38%22%2C%22333.999.fp.risk_5851F775%22%3A%22182D0E7A15F%22%2C%22333.937.fp.risk_5851F775%22%3A%22182D0ACE593%22%2C%22333.47.fp.risk_5851F775%22%3A%22182B7A55921%22%2C%22444.8.fp.risk_5851F775%22%3A%22182D0A9F4DF%22%2C%22333.788.fp.risk_5851F775%22%3A%22182CFCFA5D2%22%2C%22333.337.fp.risk_5851F775%22%3A%22182D0BB02A0%22%2C%22448.4077.fp.risk_5851F775%22%3A%22182CFCB89BD%22%2C%22333.1193.fp.risk_5851F775%22%3A%22182D0E7A1D0%22%2C%22333.859.fp.risk_5851F775%22%3A%22182D0AAEA8A%22%2C%22333.807.fp.risk_5851F775%22%3A%22182C1A1CE3F%22%2C%22888.72113.fp.risk_5851F775%22%3A%22182CAF54019%22%2C%22333.976.fp.risk_5851F775%22%3A%22182CBA4F31A%22%2C%22448.2065.fp.risk_5851F775%22%3A%22182CBB28E93%22%2C%22448.4327.fp.risk_5851F775%22%3A%22182CBB2D4E9%22%2C%22888.62483.fp.risk_5851F775%22%3A%22182CBB6DE24%22%7D%7D; bsource=share_source_copy_link; fingerprint3=29d0ba6d103d09bdd2c6e388e70e911d; fingerprint=7acca304fe40926b486cda0bf48d97f5; PEA_AU=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJiaWQiOjE5MDU3MDIzNzUsInBpZCI6MTQ3MTY2MiwiZXhwIjoxNjk1MzkxNzc2LCJpc3MiOiJ0ZXN0In0.k5g06WwSUcmKaXwLttjs7jRyCj-kmIYKlsHXPbcwzvg; i-wanna-go-feeds=2; CURRENT_QUALITY=116; blackside_state=1; buvid_fp=7acca304fe40926b486cda0bf48d97f5; bp_video_offset_1905702375=711626886569001000; innersign=0; addressId=0; canvasFp=3b8dc02ac30821c4bcde5d09821991d6; webglFp=e59dbf94f53a512cec2e9d154aef83d1; screenInfo=2560*1440*24; feSign=f389e6330b0b9eda8e82f980d3e2f7a0; payParams=%7B%22customerId%22%3A10002%2C%22serviceType%22%3A0%2C%22orderId%22%3A%22325574548%22%2C%22orderCreateTime%22%3A1664555417000%2C%22orderExpire%22%3A3600%2C%22feeType%22%3A%22CNY%22%2C%22payAmount%22%3A2000%2C%22originalAmount%22%3A2000%2C%22deviceType%22%3A2%2C%22deviceInfo%22%3A%22WEB%22%2C%22notifyUrl%22%3A%22http%3A//mall.bilibili.co/mall-trade/order/pay/callback%22%2C%22productId%22%3A%2210116575%22%2C%22productUrl%22%3A%22http%3A//mall.bilibili.com/orderlist.html%3Fstatus%3D0%22%2C%22showTitle%22%3A%22%u865A%u62DF%u7231%u8C46101%uFF01%u865A%u62DF%u5076%u50CF%u624B%u529E%u5468%u8FB9%u5927%u793C%u5305%u7B49%u4F60PICK%7E%22%2C%22showContent%22%3A%22%u865A%u62DF%u7231%u8C46101%uFF01%u865A%u62DF%u5076%u50CF%u624B%u529E%u5468%u8FB9%u5927%u793C%u5305%u7B49%u4F60PICK%7E%22%2C%22createIp%22%3A%22183.193.144.97%22%2C%22createUa%22%3A%22Mozilla/5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit/537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome/105.0.0.0%20Safari/537.36%22%2C%22returnUrl%22%3A%22https%3A//mall.bilibili.com/paycompletion.html%3ForderId%3D4000195778581487%26from%3Dsuccess%26noTitleBar%3D1%22%2C%22failUrl%22%3A%22https%3A//mall.bilibili.com/detail.html%3FloadingShow%3D1%26noTitleBar%3D1%26itemsId%3D10116575%22%2C%22extData%22%3A%22%7B%5C%22orderId%5C%22%3A4000195778581487%7D%22%2C%22traceId%22%3A%221664555417490%22%2C%22timestamp%22%3A1664555417490%2C%22version%22%3A%221.0%22%2C%22signType%22%3A%22MD5%22%2C%22sign%22%3A%22fa7f3eba3dd0cd244cc789c4a90f5f4e%22%2C%22defaultChoose%22%3A%22alipay%22%2C%22uid%22%3A1905702375%7D; c=SMzvy8H1-1664555418446-0cf296839acbc-556816134; _fmdata=aoCFwReFhbvRRYDCCM4jbQA3FztG2yJ1ZNELExB6QHD1Z2VwzGAGO5sYjvy4%2BudjRCAmz2p%2BoDB0dw8HiT0i6w%3D%3D; _xid=Dk9wH4tzcScZTFIuIU7wjeZiaQxgblB4M5WdDbED3tMa%2BU97Fz7alSGS7LUIDkNCmhRzymKlnqujRLc%2F%2BU6RZA%3D%3D; CURRENT_FNVAL=4048; PVID=19; kfcFrom=cms_5180_M79EHYXun7i7_; from=cms_5180_M79EHYXun7i7_; kfcSource=mall_8384_banner; msource=mall_8384_banner; b_lsid=332C10465_1838FC79798; LIVE_BUVID=AUTO6916645664543402"
    b.b_timer_res(b.get_b_timer_from_cookie(ck))
    # print(bapi.timeshift(int('8CFC1837', 16) / 1000))
    # print(int('8CFC1837', 16))
