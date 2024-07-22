"""
直接请求https://api.bilibili.com/x/gaia-vgate/v1/register 获取极验 这个v_voucher必须是第一次激活，不允许多次激活
data:```
v_voucher=voucher_f56bc359-4558-4b54-bfc6-685016efb598
```
Header不变，加上个Referer即可
响应
```
{
  "code": 0,
  "message": "0",
  "ttl": 1,
  "data": {
    "type": "geetest",
    "token": "ad70400460234be69e6028cfbfca2baa",
    "geetest": {
      "challenge": "5d18e4a4376297823c68a48a47162110",
      "gt": "ac597a4506fee079629df5d8b66dd4fe"
    },
    "biliword": null,
    "phone": null,
    "sms": null
  }
}
```

验证完成之后调用https://api.bilibili.com/x/gaia-vgate/v1/validate post验证一下
```
{challenge: 5d18e4a4376297823c68a48a47162110
seccode: 92de0515cc6d566587828b24c7891287|jordan
token: ad70400460234be69e6028cfbfca2baa
validate: 92de0515cc6d566587828b24c7891287}
```

"""
import os
import time
from typing import Union
from curl_cffi import requests

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import CONFIG
from grpc获取动态.Utils.极验.models.captcha_models import CaptchaResultInfo, GeetestRegInfo, GeetestSuccessTimeCalc
from grpc获取动态.Utils.极验.util.utils_get_target_center_position import CaptchaDetector
import bili_ticket_gt_python


# TODO:开发新的图像匹配方法，主要用于生成成本矩阵
class GeetestV3Breaker:
    def __init__(self):
        self.log = logger.bind(user='GeetestV3Breaker')
        self.current_file_root_dir = os.path.dirname(os.path.abspath(__file__))  # 就是当前文件的路径目录
        self.driver = None
        self.wait = None
        self.captcha_detector = None
        self.geetest_validator_html_path = "file://" + os.path.join(self.current_file_root_dir,
                                                                    'Geetest_html/geetest-validator/index.html')
        # 本地极验校验工具的路径
        self.succ_stats = GeetestSuccessTimeCalc()
        self.click = bili_ticket_gt_python.ClickPy()

    def init_det(self):
        self.captcha_detector = CaptchaDetector.Instance()

    def init_browser(self):
        self.log.info('初始化了一个selenium')

        options = Options()
        options.binary_location = 'C:/WebDriver/chrome.exe'
        self.driver = webdriver.Chrome(service=Service('C:/WebDriver/bin/chromedriver.exe'), options=options)
        self.wait = WebDriverWait(driver=self.driver, timeout=10, poll_frequency=0.5)


    def _step1_input_gt_challenge(self, gt, challenge):
        gt_text_box = self.driver.find_element(By.CSS_SELECTOR, '.inp[id=gt]')
        gt_text_box.clear()
        gt_text_box.send_keys(gt)
        challeng_text_box = self.driver.find_element(By.CSS_SELECTOR, '.inp[id=challenge]')
        challeng_text_box.clear()
        challeng_text_box.send_keys(challenge)

    def _step2_click_generate_btn(self):
        generate_btn = self.driver.find_element(By.CSS_SELECTOR, '.btn[id=btn-gen]')
        generate_btn.click()
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".geetest_radar_tip")))  # 等待验证码生成
        captcha_btn = self.driver.find_element(By.CSS_SELECTOR, '.geetest_radar_tip')
        captcha_btn.click()  # 点击生成验证码modal，弹出验证码界面

    def _step3_break_geetest_validation(self) -> CaptchaResultInfo:
        geetest_item_img = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".geetest_item_img")),
                                           message="极验验证码加载失败")
        geetest_tip_img = self.driver.find_element(By.CSS_SELECTOR, '.geetest_tip_img')
        tip_img_style = geetest_tip_img.get_attribute('style')
        picurl = tip_img_style[tip_img_style.find('https'):tip_img_style.find('");')]
        captcha_result_info = self.captcha_detector.detect(picurl)
        if captcha_result_info.target_centers is None:
            self.log.error(f'验证码识别失败，请重新尝试，错误信息：{captcha_result_info.img_name}')
            geetest_refresh = self.driver.find_element(By.CSS_SELECTOR, '.geetest_refresh')
            geetest_refresh.click()
            self.succ_stats.total_time += 1
            return self._step3_break_geetest_validation()
        ac = ActionChains(self.driver)
        ac.move_to_element_with_offset(geetest_item_img, -geetest_item_img.rect['width'] / 2,
                                       -geetest_item_img.rect['height'] / 2).pause(0.1)
        c_x, c_y = 0, 0
        for x, y in captcha_result_info.target_centers:
            path_x, path_y = x - c_x, y - c_y
            print(f'移动距离：{path_x}，{path_y}')
            ac = ac.move_by_offset(path_x, path_y).click().pause(0.1)
            c_x, c_y = x, y

        ac.perform()
        geetest_commit_tip = self.driver.find_element(By.CSS_SELECTOR, '.geetest_commit_tip')
        geetest_commit_tip.click()
        return captcha_result_info

    def _step4_get_validation(self) -> Union[str, None]:
        """
        获取最终结果
        :return:
        """
        geetest_success_radar_tip_content = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".geetest_success_radar_tip_content")),
            message='等待`极验成功提示`失败！可能是验证码识别错了！')
        tip_content = geetest_success_radar_tip_content.text
        print(tip_content)

        if tip_content == '验证成功':
            time.sleep(1)
            btn_result = self.driver.find_element(By.CSS_SELECTOR, '#btn-result')
            btn_result.click()
            validate = self.driver.find_element(By.CSS_SELECTOR, '#validate')
            return validate.get_property('value')

        return None

    def break_geetest(self, gt, challenge) -> Union[str, None]:
        if not self.driver.current_window_handle:
            self.driver = webdriver.Chrome()
        if 'file' not in self.driver.current_url:
            self.driver.get(self.geetest_validator_html_path)
        self._step1_input_gt_challenge(gt, challenge)
        time.sleep(0.5)
        self._step2_click_generate_btn()
        time.sleep(0.5)
        captcha_result_info = self._step3_break_geetest_validation()
        if captcha_result_info.target_centers is None:
            self.log.warning(f'识别验证码失败！')
            return None
        if validattion := self._step4_get_validation():
            return validattion

        self.captcha_detector.save_draw_rectangle(captcha_result_info.origin_img, captcha_result_info.bboxes,
                                                  self.captcha_detector.log_path.detect_failed_pic + f'geetest_validate_fail_{captcha_result_info.img_name}')
        return None

    # region 静态方法，获取极验信息和验证用
    @staticmethod
    def get_geetest_reg_info(v_voucher: str,
                             ua: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 "
                                       "Safari/537.36 Edg/125.0.0.0") -> Union[GeetestRegInfo, bool]:
        data = {
            "v_voucher": v_voucher
        }
        headers = {
            'Accept': 'application/json, text/plain, */* ',
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://www.bilibili.com",
            "Referer": "http://www.bilibili.com/",
            "User-Agent": ua,
        }
        req: requests.Response = requests.post('https://api.bilibili.com/x/gaia-vgate/v1/register', data=data,
                                               headers=headers, proxies={
                'http': CONFIG.CONFIG.my_ipv6_addr,
                'https': CONFIG.CONFIG.my_ipv6_addr
            })
        resp_json = req.json()
        if resp_json.get('code') == 0:
            if resp_json.get('data').get('geetest') is None:
                logger.error(f"\n获取极验信息失败: {resp_json}\n{req.headers}")
                return False
            logger.debug(f"\n成功获取极验challenge：{resp_json}")
            return GeetestRegInfo(
                type=resp_json.get('data').get('type'),
                token=resp_json.get('data').get('token'),
                geetest_challenge=resp_json.get('data').get('geetest').get('challenge'),
                geetest_gt=resp_json.get('data').get('geetest').get('gt')
            )
        else:
            logger.error(f"\n获取极验信息失败: {resp_json}")
            return False

    @staticmethod
    def validate_geetest(challenge, token, validate,
                         ua: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 "
                                   "Safari/537.36 Edg/125.0.0.0") -> bool:
        data = {
            "challenge": challenge,
            "seccode": validate + "|jordan",
            "token": token,
            "validate": validate
        }
        headers = {
            'Accept': 'application/json, text/plain, */* ',
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://t.bilibili.com",
            "Referer": "http://t.bilibili.com/",
            "User-Agent": ua,
        }
        req = requests.post('https://api.bilibili.com/x/gaia-vgate/v1/validate', data=data, headers=headers, proxies={
            'http': CONFIG.CONFIG.my_ipv6_addr,
            'https': CONFIG.CONFIG.my_ipv6_addr
        })
        resp_json = req.json()
        if resp_json.get('code') != 0:
            logger.error(f"\n验证validate极验失败:{challenge, token, validate}\n {resp_json}")
            return False
        logger.debug(f'\n验证成功：{resp_json}')
        return True

    # endregion

    def validate_form_voucher_ua(self, v_voucher: str,
                                 ua: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 "
                                           "Safari/537.36 Edg/125.0.0.0",
                                 use_bili_ticket_gt=True):
        self.log.info(
            f'\n当前成功率：{self.succ_stats.calc_succ_rate()}\n成功数：{self.succ_stats.succ_time}\t总尝试数：{self.succ_stats.total_time}')
        try:
            geetest_reg_info = GeetestV3Breaker.get_geetest_reg_info(v_voucher, ua)
            if geetest_reg_info is False:
                return False
            # 验证码获取成功才加1
            self.succ_stats.total_time += 1
            if use_bili_ticket_gt:
                if validation := self.click.simple_match_retry(geetest_reg_info.geetest_gt,
                                                               geetest_reg_info.geetest_challenge):
                    self.log.debug(f'\nbili_ticket_gt_python验证码获取成功：{validation}')
                    validate_result = GeetestV3Breaker.validate_geetest(geetest_reg_info.geetest_challenge,
                                                                        geetest_reg_info.token,
                                                                        validation)
                    if validate_result:
                        self.succ_stats.succ_time += 1
            else:
                if geetest_reg_info:
                    if self.driver is None:
                        self.init_browser()
                        self.init_det()
                    if validation := self.break_geetest(geetest_reg_info.geetest_gt,
                                                        geetest_reg_info.geetest_challenge):
                        validate_result = GeetestV3Breaker.validate_geetest(
                            geetest_reg_info.geetest_challenge,
                            geetest_reg_info.token,
                            validation)
                        if validate_result:
                            self.succ_stats.succ_time += 1
                elif not geetest_reg_info:
                    self.succ_stats.total_time -= 1

        except Exception as e:
            if str(e) == 'RuntimeError: bili_ticket极验模块错误 { 错误类型: MissingParam("data") }':
                return
            self.log.exception(e)
            self.succ_stats.total_time -= 1
        finally:
            if use_bili_ticket_gt:
                pass
            else:
                try:
                    _ = self.driver.current_window_handle
                except:
                    self.driver = webdriver.Chrome()
                self.driver.refresh()  # 用本地的html，不管成功还是失败，每次执行结束都直接刷新


if __name__ == '__main__':
    while 1:
        vc = input('输入极验voucher:').strip()
        res = GeetestV3Breaker.get_geetest_reg_info(vc)
        print(res)
