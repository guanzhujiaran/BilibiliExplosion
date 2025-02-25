import asyncio
import json
import os
import time
from typing import Union
import requests
import httpx
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from CONFIG import CONFIG
from fastapi接口.log.base_log import Voucher352_logger
from fastapi接口.service.geetest_captcha.jy_click_captcha import jy_click
from grpc获取动态.Utils.UserAgentParser import UserAgentParser
from grpc获取动态.Utils.极验.models.captcha_models import CaptchaResultInfo, GeetestRegInfo, GeetestSuccessTimeCalc
import bili_ticket_gt_python
from grpc获取动态.grpc.bapi.biliapi import appsign, get_geetest_reg_info, validate_geetest
from grpc获取动态.Utils.metadata.makeMetaData import gen_trace_id


class GeetestV3Breaker:
    def __init__(self):
        self.log = Voucher352_logger
        self.current_file_root_dir = os.path.dirname(os.path.abspath(__file__))  # 就是当前文件的路径目录
        self.driver = None
        self.wait = None
        self.captcha_detector=None
        self.geetest_validator_html_path = "file://" + os.path.join(self.current_file_root_dir,
                                                                    'Geetest_html/geetest-validator/index.html')
        # 本地极验校验工具的路径
        self.succ_stats = GeetestSuccessTimeCalc()
        self.click = None

    def init_det(self):
        if not self.captcha_detector:
            from grpc获取动态.Utils.极验.util.utils_get_target_center_position import captcha_detector
            self.captcha_detector = captcha_detector

    def init_browser(self,headless:bool=True):
        self.log.info('初始化了一个selenium')
        options = Options()
        if headless:
            options.add_argument('--headless')
        self.driver = webdriver.Edge(service=Service(CONFIG.selenium_config.edge_path), options=options)
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

    def _step3_break_geetest_validation(self, use_jy_click: bool) -> CaptchaResultInfo:
        geetest_item_img = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".geetest_item_img")),
                                           message="极验验证码加载失败")
        geetest_tip_img = self.driver.find_element(By.CSS_SELECTOR, '.geetest_tip_img')
        tip_img_style = geetest_tip_img.get_attribute('style')
        picurl = tip_img_style[tip_img_style.find('https'):tip_img_style.find('");')]
        if use_jy_click:
            captcha_result_info: CaptchaResultInfo = jy_click(picurl)
        else:
            captcha_result_info: CaptchaResultInfo = self.captcha_detector.detect(picurl)
        if captcha_result_info.target_centers is None:
            self.log.error(f'验证码识别失败，请重新尝试，错误信息：{captcha_result_info.img_name}')
            geetest_refresh = self.driver.find_element(By.CSS_SELECTOR, '.geetest_refresh')
            geetest_refresh.click()
            self.succ_stats.total_time += 1
            return self._step3_break_geetest_validation(use_jy_click)
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

    def break_geetest(self, gt, challenge, use_jy_click=False) -> Union[str, None]:
        if not self.driver.current_window_handle:
            self.driver = webdriver.Edge()
        if 'file' not in self.driver.current_url:
            self.driver.get(self.geetest_validator_html_path)
        self._step1_input_gt_challenge(gt, challenge)
        time.sleep(0.5)
        self._step2_click_generate_btn()
        time.sleep(0.5)
        captcha_result_info = self._step3_break_geetest_validation(use_jy_click)
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
                                       "Safari/537.36 Edg/125.0.0.0",
                             ck: str = "",
                             ori: str = "",
                             ref: str = "",
                             ticket: str = "",
                             version: str = "8.9.0"
                             ) -> Union[GeetestRegInfo, bool]:
        data = {
            "disable_rcmd": 0,
            "mobi_app": "android",
            "platform": "android",
            "statistics": json.dumps({"appId": 1, "platform": 3, "version": version, "abtest": ""},
                                     separators=(',', ':')),
            "ts": int(time.time()),
            "v_voucher": v_voucher,
        }
        data = appsign(data)
        headers_raw = [
            ('native_api_from', 'h5'),
            ("cookie", f'Buvid={ck}' if ck else ''),
            ('buvid', ck if ck else ''),
            ('accept', 'application/json, text/plain, */*'),
            ("referer", "https://www.bilibili.com/h5/risk-captcha"),
            ('env', 'prod'),
            ('app-key', 'android'),
            ('env', 'prod'),
            ('app-key', 'android'),
            ("user-agent", ua),
            ('x-bili-trace-id', gen_trace_id()),
            ("x-bili-aurora-eid", ''),
            ('x-bili-mid', ''),
            ('x-bili-aurora-zone', ''),
            ('x-bili-gaia-vtoken', ''),
            ('x-bili-ticket', ticket),
            ('content-type', 'application/x-www-form-urlencoded; charset=utf-8'),
            ('accept-encoding', 'gzip')
        ]
        # data = urllib.parse.urlencode(data)
        response: requests.Response = httpx.request(
            method='POST',
            url='https://api.bilibili.com/x/gaia-vgate/v1/register',
            data=data,
            headers=headers_raw,
            # proxies={
            #     'http://': CONFIG.CONFIG.my_ipv6_addr,
            #     'https://': CONFIG.CONFIG.my_ipv6_addr
            # }
        )
        resp_json = response.json()
        if resp_json.get('code') == 0:
            if resp_json.get('data').get('geetest') is None:
                Voucher352_logger.error(
                    f"\n获取极验信息失败: {resp_json}\n请求头：{headers_raw}\n响应头：{response.headers}")
                return False
            Voucher352_logger.debug(f"\n成功获取极验challenge：{resp_json}")
            return GeetestRegInfo(
                type=resp_json.get('data').get('type'),
                token=resp_json.get('data').get('token'),
                geetest_challenge=resp_json.get('data').get('geetest').get('challenge'),
                geetest_gt=resp_json.get('data').get('geetest').get('gt')
            )
        else:
            Voucher352_logger.error(f"\n获取极验信息失败: {resp_json}")
            return False

    @staticmethod
    def validate_geetest(challenge, token, validate,
                         ua: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 "
                                   "Safari/537.36 Edg/125.0.0.0",
                         ck: str = "",
                         ori: str = "",
                         ref: str = "",
                         ticket: str = "",
                         version: str = "8.9.0"
                         ) -> str:
        """
        :param challenge:
        :param token:
        :param validate:
        :param ua:
        :return:
        """
        url = 'https://api.bilibili.com/x/gaia-vgate/v1/validate'
        data = {
            "challenge": challenge,
            "disable_rcmd": 0,
            "mobi_app": "android",
            "platform": "android",
            "seccode": validate + "|jordan",
            "statistics": json.dumps({"appId": 1, "platform": 3, "version": version, "abtest": ""},
                                     separators=(',', ':')),
            "token": token,
            "ts": int(time.time()),
            "validate": validate
        }
        data = appsign(data)
        headers_raw = [
            ('native_api_from', 'h5'),
            ("cookie", f'Buvid={ck}' if ck else ''),
            ('buvid', ck if ck else ''),
            ('accept', 'application/json, text/plain, */*'),
            ("referer", "https://www.bilibili.com/h5/risk-captcha"),
            ('env', 'prod'),
            ('app-key', 'android'),
            ('env', 'prod'),
            ('app-key', 'android'),
            ("user-agent", ua),
            ('x-bili-trace-id', gen_trace_id()),
            ("x-bili-aurora-eid", ''),
            ('x-bili-mid', ''),
            ('x-bili-aurora-zone', ''),
            ('x-bili-gaia-vtoken', ''),
            ('x-bili-ticket', ticket),
            ('content-type', 'application/x-www-form-urlencoded; charset=utf-8'),
            ('accept-encoding', 'gzip')
        ]
        # data = urllib.parse.urlencode(data)
        req = httpx.request(
            method='POST',
            url=url,
            data=data,
            headers=headers_raw,
            # proxies={
            #     'http://': CONFIG.CONFIG.my_ipv6_addr,
            #     'https://': CONFIG.CONFIG.my_ipv6_addr
            # }
        )
        resp_json = req.json()
        if resp_json.get('code') != 0:
            Voucher352_logger.error(
                f"\n发请求 {url} 验证validate极验失败:{challenge, token, validate}\n {resp_json}\n{data}\n{headers_raw}")
            return ''
        Voucher352_logger.debug(f'\n发请求验证成功：{resp_json}')
        return token

    # endregion

    def validate_form_voucher_ua(self, v_voucher: str,
                                 ua: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 "
                                           "Safari/537.36 Edg/125.0.0.0",
                                 ck: str = "",
                                 ori: str = "",
                                 ref: str = "",
                                 ticket: str = "",
                                 version: str = "",
                                 session_id: str = "",
                                 use_bili_ticket_gt=True,
                                 use_jy_click_selenium=False
                                 ) -> str:
        h5_ua = UserAgentParser.parse_h5_ua(ua, ck, session_id=session_id)
        self.log.info(
            f'\n当前成功率：{self.succ_stats.calc_succ_rate()}\n成功数：{self.succ_stats.succ_time}\t总尝试数：{self.succ_stats.total_time}')
        if self.driver is None:
            if use_bili_ticket_gt or use_jy_click_selenium:
                self.init_browser()
            if use_bili_ticket_gt:
                self.init_det()
        try:
            geetest_reg_info = GeetestV3Breaker.get_geetest_reg_info(v_voucher, h5_ua, ck, ori, ref, ticket=ticket,
                                                                     version=version)
            if geetest_reg_info is False:
                return ""
            # 验证码获取成功才加1
            self.succ_stats.total_time += 1
            if use_bili_ticket_gt:
                if not self.click:
                    self.click = bili_ticket_gt_python.ClickPy()
                if validation := self.click.simple_match_retry(geetest_reg_info.geetest_gt,
                                                               geetest_reg_info.geetest_challenge):
                    self.log.debug(f'\nbili_ticket_gt_python验证码获取成功：{validation}')
                    validate_result = GeetestV3Breaker.validate_geetest(
                        geetest_reg_info.geetest_challenge,
                        geetest_reg_info.token,
                        validation,
                        h5_ua,
                        ck,
                        ori,
                        ref,
                        ticket=ticket,
                        version=version
                    )
                    if validate_result:
                        self.succ_stats.succ_time += 1
                    return validate_result
            else:
                if geetest_reg_info:
                    if validation := self.break_geetest(
                            geetest_reg_info.geetest_gt,
                            geetest_reg_info.geetest_challenge,
                            use_jy_click=use_jy_click_selenium
                    ):
                        validate_result = GeetestV3Breaker.validate_geetest(
                            challenge=geetest_reg_info.geetest_challenge,
                            token=geetest_reg_info.token,
                            validate=validation,
                            ua=h5_ua,
                            ck=ck,
                            ori=ori,
                            ref=ref,
                            ticket=ticket,
                            version=version
                        )
                        if validate_result:
                            self.succ_stats.succ_time += 1
                        return validate_result
                elif not geetest_reg_info:
                    self.succ_stats.total_time -= 1
                    return ''
        except Exception as e:
            if str(e) == 'RuntimeError: bili_ticket极验模块错误 { 错误类型: MissingParam("data") }':
                return ''
            self.log.error(f'极验验证失败！{e}')
            self.succ_stats.total_time -= 1
        finally:
            if use_bili_ticket_gt:
                pass
            else:
                self.driver.refresh()  # 用本地的html，不管成功还是失败，每次执行结束都直接刷新

    async def a_validate_form_voucher_ua(self, v_voucher: str,
                                         ua: str = "Dalvik/2.1.0 (Linux; U; Android 9; PCRT00 Build/PQ3A.190605.05081124) 8.13.0 os/android model/PCRT00 mobi_app/android build/8130300 channel/master innerVer/8130300 osVer/9 network/2",
                                         ck: str = "",
                                         ori: str = "",
                                         ref: str = "",
                                         ticket: str = "",
                                         version: str = "",
                                         session_id: str = "",
                                         use_bili_ticket_gt=True,
                                         use_jy_click_selenium=False):
        h5_ua = UserAgentParser.parse_h5_ua(ua, ck, session_id=session_id)
        self.log.info(
            f'\n当前成功率：{self.succ_stats.calc_succ_rate()}\n成功数：{self.succ_stats.succ_time}\t总尝试数：{self.succ_stats.total_time}')
        if self.driver is None:
            if use_bili_ticket_gt or use_jy_click_selenium:
                self.init_browser()
            if use_bili_ticket_gt:
                self.init_det()
        try:
            geetest_reg_info = await get_geetest_reg_info(v_voucher, h5_ua, ck, ori, ref, ticket=ticket,
                                                          version=version)
            if geetest_reg_info is False:
                return ''
            # 验证码获取成功才加1
            self.succ_stats.total_time += 1
            if use_bili_ticket_gt:
                if not self.click:
                    self.click = bili_ticket_gt_python.ClickPy()
                if validation := self.click.simple_match_retry(geetest_reg_info.geetest_gt,
                                                               geetest_reg_info.geetest_challenge):
                    self.log.debug(f'\nbili_ticket_gt_python验证码获取成功：{validation}')
                    validate_result = await validate_geetest(
                        geetest_reg_info.geetest_challenge,
                        geetest_reg_info.token,
                        validation,
                        h5_ua,
                        ck,
                        ori,
                        ref,
                        ticket=ticket,
                        version=version
                    )
                    if validate_result:
                        self.succ_stats.succ_time += 1
                    return validate_result
            else:
                if geetest_reg_info:
                    if validation := await asyncio.to_thread(self.break_geetest,
                                                             geetest_reg_info.geetest_gt,
                                                             geetest_reg_info.geetest_challenge,
                                                             use_jy_click_selenium,
                                                             ):
                        validate_result = await validate_geetest(
                            challenge=geetest_reg_info.geetest_challenge,
                            token=geetest_reg_info.token,
                            validate=validation,
                            h5_ua=h5_ua,
                            buvid=ck,
                            ori=ori,
                            ref=ref,
                            ticket=ticket,
                            version=version
                        )
                        if validate_result:
                            self.succ_stats.succ_time += 1
                        return validate_result
                elif not geetest_reg_info:
                    self.succ_stats.total_time -= 1
                    return ''
        except Exception as e:
            if str(e) == 'RuntimeError: bili_ticket极验模块错误 { 错误类型: MissingParam("data") }':
                return ''
            self.log.debug(e)
            self.succ_stats.total_time -= 1
        finally:
            if use_bili_ticket_gt:
                pass
            else:
                self.driver.refresh()  # 用本地的html，不管成功还是失败，每次执行结束都直接刷新


if __name__ == '__main__':
    _g = GeetestV3Breaker()
    asyncio.run(_g.a_validate_form_voucher_ua(
        v_voucher=''
    ))
