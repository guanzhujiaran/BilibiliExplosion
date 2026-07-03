import asyncio
import os
import bili_ticket_gt_python
from log.base_log import Voucher352_logger
from Utils.GrpcUtils.UserAgentParser import UserAgentParser
from Utils.GrpcUtils.极验.models.captcha_models import GeetestSuccessTimeCalc
from Service.GrpcModule.Grpc.Bapi.GeetestHandler import get_geetest_reg_info, validate_geetest


class GeetestV3Breaker:
    def __init__(self):
        self.log = Voucher352_logger
        self.current_file_root_dir = os.path.dirname(os.path.abspath(__file__))  # 就是当前文件的路径目录
        # 本地极验校验工具的路径
        self.succ_stats = GeetestSuccessTimeCalc()
        self.click = bili_ticket_gt_python.ClickPy()

    async def a_validate_form_voucher_ua(self, v_voucher: str,
                                         ua: str = "Dalvik/2.1.0 (Linux; U; Android 9; PCRT00 Build/PQ3A.190605.05081124) 8.13.0 os/android model/PCRT00 mobi_app/android build/8130300 channel/master innerVer/8130300 osVer/9 network/2",
                                         ck: str = "",
                                         ori: str = "",
                                         ref: str = "",
                                         ticket: str = "",
                                         version: str = "",
                                         session_id: str = "",
                                         use_bili_ticket_gt=True, ):
        """
        极验点击验证码
        :param v_voucher:
        :param ua:
        :param ck: 传buvid的值就行了
        :param ori:
        :param ref:
        :param ticket:
        :param version:
        :param session_id:
        :param use_bili_ticket_gt:
        :return:
        """
        h5_ua = UserAgentParser.parse_h5_ua(ua, ck, session_id=session_id)
        self.log.info(
            f'\n当前成功率：{self.succ_stats.calc_succ_rate()}\n成功数：{self.succ_stats.succ_time}\t总尝试数：{self.succ_stats.total_time}')
        try:
            geetest_reg_info = await get_geetest_reg_info(v_voucher, h5_ua, ck, ori, ref, ticket=ticket,
                                                          version=version)
            if geetest_reg_info is False:
                return ''
            # 验证码获取成功才加1
            self.succ_stats.total_time += 1
            if 1 or use_bili_ticket_gt:
                gt, challenge = geetest_reg_info.geetest_gt, geetest_reg_info.geetest_challenge
                if validation := await asyncio.to_thread(self.click.simple_match_retry, gt, challenge):
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
        except Exception as e:
            self.log.warning(f'极验验证失败！{e}')
            self.succ_stats.total_time -= 1
        finally:
            ...


geetest_v3_breaker = GeetestV3Breaker()
if __name__ == '__main__':
    _g = GeetestV3Breaker()
    asyncio.run(_g.a_validate_form_voucher_ua(
        v_voucher=''
    ))
