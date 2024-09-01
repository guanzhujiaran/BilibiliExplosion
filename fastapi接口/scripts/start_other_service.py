import asyncio
import io
import os
import sys
import time
import multiprocessing as mp
from threading import Thread
from types import MethodType
from loguru import logger
sys.path.append(os.path.dirname(os.path.join(__file__, '../../../')))  # 将CONFIG导入
from CONFIG import CONFIG
sys.path.extend([
    x.value for x in CONFIG.project_path
])
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class OtherService:
    log = logger.bind(user='OtherService')
    show_log = True

    def start_bili_up_space_monitor(self):
        """
        监控b站up主空间
        :return:
        """
        from grpc获取动态.src.监控up动态.bili_dynamic_monitor import monitor
        a = monitor()
        asyncio.run(a.main(show_log=self.show_log))

    def schedule_get_charge_and_official_lot(self):
        """
        定时获取up主充电和官方抽奖
        :return:
        """
        from opus新版官方抽奖.转发抽奖.定时获取所有动态以及发布充电和官方抽奖专栏 import schedule_get_official_lot_main
        schedule_get_official_lot_main(show_log=self.show_log)

    def schedule_get_reserve_lot(self):
        """
        定时获取预约抽奖
        :return:
        """
        from opus新版官方抽奖.预约抽奖.etc.schedule_get_reserve_lot import schedule_get_reserve_lot_main
        schedule_get_reserve_lot_main(show_log=self.show_log)

    def monitor_ipv6_change(self):
        from 光猫测试.监控本地ip地址变化 import monitor_ipv6_address_changes
        monitor_ipv6_address_changes()

    def bili_live_monitor(self):
        """
        b站天选监控
        :return:
        """
        from src.monitor import Monitor
        m = Monitor()
        m.main(ShowLog=False)

    def _352_geetest_mq_client(self):
        """
        极验验证码
        :return:
        """
        from grpc获取动态.Utils.MQClient.VoucherMQClient import VoucherMQClient
        t_set = set()
        for i in range(3):
            __ = VoucherMQClient()
            thread = Thread(target=__.start_voucher_break_consumer)
            thread.start()
            t_set.add(thread)
        for i in t_set:
            i.join()


def start_scripts():
    p_set = set()
    ots = OtherService()
    for i in ots.__dir__():
        m = getattr(ots, i)
        if type(m) is MethodType:
            p = mp.Process(target=m, name=i, daemon=False)
            logger.info(f'执行方法：{i}')
            p.start()
            p_set.add(p)
    while 1:
        info_text = ''
        for p in p_set:
            info_text += f'\n进程【{p.name}】状态：is_alive:{p.is_alive()}'
        logger.info(info_text)
        time.sleep(30)


if __name__ == '__main__':
    start_scripts()
