# -*- coding: utf-8 -*-
import asyncio
import os.path
import re
import socket
import time
from typing import Literal
from fastapi接口.log.base_log import ipv6_monitor_logger
from fastapi接口.service.ipinfo.get_ipv6 import set_ipv6_to_redis, get_ipv6_from_redis
from fastapi接口.service.MQ.base.MQServer.Ipv6ChangeMQServer import Ipv6ChangeRabbitMQ
from utl.pushme.pushme import pushme, pushme_try_catch_decorator, async_pushme_try_catch_decorator
from fastapi接口.scripts.光猫ip.获取本机ipv6 import ipv6Obj

net_adpater_name = '"vEthernet (wsl-bg)"'

_loop = asyncio.new_event_loop()


def bat_gen(prefix: str, operation: Literal['del', 'add'], bat_file_path):
    bat_file = open(bat_file_path, "w", encoding="utf-8")
    # 修改为你的 ipv6 前缀
    # maxprefix = ':'.join(prefix.split(':')[:-1]) + ":" + hex(int(prefix.split(":")[-1], 16) + 15)[2:]  # 最大前缀
    suffix = 'b'
    need_num = 32
    bat_data = []
    main_ipv6 = [prefix + ":" + hex(i)[2:] for i in range(255)]
    for i in range(need_num):
        all_str = hex(int(suffix, 16) + (i // 16) * 16)[2:].rjust(12, '0')
        all_str_list = re.findall('.{4}', all_str)
        bat_data.append(main_ipv6[i % 16] + ":" + ":".join(all_str_list))

    # 自己的网卡名字 ipconfig查看
    bat_data = [f"""netsh interface ipv6 {operation} address {net_adpater_name} {i}""" for i in bat_data]
    bat_file.write("\n".join(bat_data))
    bat_file.close()


def bat_gen_by_ip_list(ipv6_list: list, operation: Literal['del', 'add'], bat_file_path, prefix):
    if (len(ipv6_list) < 5 and operation == "add"):
        return bat_gen(prefix, "add", bat_file_path)
    bat_file = open(bat_file_path, "w", encoding="utf-8")
    bat_data = [f"""netsh interface ipv6 {operation} address {net_adpater_name} {i}""" for i in ipv6_list if
                "::" in i or operation == 'del']
    bat_file.write("\n".join(bat_data) + "\n")
    bat_file.close()


def exec_bat(bat_path):
    with open(bat_path, 'r', encoding='utf-8') as f:
        cmd_str_list = f.readlines()
    for cmd_str in cmd_str_list:
        if cmd_str.strip():
            p = os.system(cmd_str.strip())
            ipv6_monitor_logger.info(f'执行bat文件中的行内容：{cmd_str.strip()} 结果：{p}')


def get_all_ipv6() -> list[str]:
    addrs = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6)
    ret_list = []
    for item in addrs:
        if 'fe80:' in item[4][0]:
            continue
        ret_list.append(item[4][0])
    return ret_list


def change_ipv6_config(now_ipv6_prefix: str, latest_ipv6_prefix: str = ''):
    """
    修改ipv6相关设置
    :param latest_ipv6_prefix:
    :param now_ipv6_prefix:
    """
    squid_config_path = 'C:/Squid/etc/squid/squid.conf'
    squid_config_example_path = os.path.join(os.path.dirname(__file__), 'squid.example.conf')
    bat_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ifconfig.bat')
    if not latest_ipv6_prefix:
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '上次的ipv6.txt')):
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '上次的ipv6.txt'), 'r') as f:
                latest_ipv6_prefix = f.read()

    latest_ipv6_list = get_all_ipv6()
    bat_gen_by_ip_list(latest_ipv6_list, 'del', bat_file_path, now_ipv6_prefix)
    exec_bat(bat_file_path)
    latest_ipv6_list = [x for x in latest_ipv6_list if latest_ipv6_prefix in x]
    now_ipv6_list = list(map(lambda x: x.replace(latest_ipv6_prefix, now_ipv6_prefix), latest_ipv6_list))
    bat_gen_by_ip_list(now_ipv6_list, 'add', bat_file_path, now_ipv6_prefix)
    exec_bat(bat_file_path)

    with open(squid_config_example_path, 'r', encoding='utf-8') as f:
        example_config = f.read()
    new_config = example_config.format(now_ipv6=now_ipv6_prefix)
    with open(squid_config_path, 'w', encoding='utf-8') as f:
        f.write(new_config)

    p = os.system(
        'C:/Squid/bin/squid -k reconfigure')
    ipv6_monitor_logger.info(p)
    time.sleep(3)
    p = os.system(
        'cd C:/Squid/bin\nsquid -z')
    ipv6_monitor_logger.info(p)


ipv6_change_mq = Ipv6ChangeRabbitMQ.Instance()


@pushme_try_catch_decorator
def monitor_ipv6_address_changes():
    ipv6_monitor_logger.info('启动监控本地ipv6地址程序！！！')
    my_ipv6 = ipv6Obj()
    previous_ipv6_address = _loop.run_until_complete(get_ipv6_from_redis())
    previous_ipv6_prefix = ':'.join(previous_ipv6_address.split(':')[0:4])  # 2409:8a1e:2a62:69a
    while True:
        current_ipv6_address = my_ipv6.get_ipv6_prefix()  # 2409:8a1e:2a62:69a0::/60
        current_ipv6_prefix = ':'.join(current_ipv6_address.split(':')[0:4])  # 2409:8a1e:2a62:69a
        # print(current_ipv6_prefix)
        ipv6_monitor_logger.info(f'当前ipv6地址：{current_ipv6_address}')
        if current_ipv6_prefix != previous_ipv6_prefix:  # 只判断前缀
            ipv6_monitor_logger.info("IPv6地址发生变化：", current_ipv6_address, int(time.time()))
            change_ipv6_config(':'.join(current_ipv6_address.split(':')[0:4]), previous_ipv6_prefix)
            # ipv6_change_mq.push_ipv6_change(previous_ipv6_address, current_ipv6_address)
            try:
                pushme(f'IPv6地址发生变化！{time.strftime("%Y-%m-%d %H:%M:%S")}',
                       f'原地址：{previous_ipv6_address}\n现地址：{current_ipv6_address}')
                _loop.run_until_complete(set_ipv6_to_redis(current_ipv6_address))
            except:
                ipv6_monitor_logger.exception('推送失败')
            previous_ipv6_address = current_ipv6_address
            previous_ipv6_prefix = ':'.join(current_ipv6_address.split(':')[0:4])
        time.sleep(40)  # 每隔30秒检查一次


@async_pushme_try_catch_decorator
async def async_monitor_ipv6_address_changes():
    ipv6_monitor_logger.info('启动监控本地ipv6地址程序！！！')
    my_ipv6 = ipv6Obj()
    # previous_ipv6_address = await get_ipv6_from_redis()
    previous_ipv6_address = ""
    previous_ipv6_prefix = ':'.join(previous_ipv6_address.split(':')[0:4])  # 2409:8a1e:2a62:69a
    while True:
        try:
            current_ipv6_address = await my_ipv6.async_get_ipv6_prefix_selenium()  # 2409:8a1e:2a62:69a0::/60
            current_ipv6_prefix = ':'.join(current_ipv6_address.split(':')[0:4])  # 2409:8a1e:2a62:69a
            ipv6_monitor_logger.info(f'当前ipv6地址：{current_ipv6_address}')
            if current_ipv6_prefix and current_ipv6_prefix != previous_ipv6_prefix:  # 只判断前缀
                ipv6_monitor_logger.critical(f"IPv6地址发生变化：{current_ipv6_address} {int(time.time())}")
                change_ipv6_config(':'.join(current_ipv6_address.split(':')[0:4]),
                                   previous_ipv6_prefix)
                try:
                    pushme(f'IPv6地址发生变化！{time.strftime("%Y-%m-%d %H:%M:%S")}',
                           f'原地址：{previous_ipv6_address}\n现地址：{current_ipv6_address}')
                    await set_ipv6_to_redis(current_ipv6_address)
                except Exception as e:
                    ipv6_monitor_logger.exception('推送失败')
                previous_ipv6_address = current_ipv6_address
                previous_ipv6_prefix = ':'.join(current_ipv6_address.split(':')[0:4])
            await asyncio.sleep(30)  # 每隔40秒检查一次
        except Exception as e:
            ipv6_monitor_logger.exception(e)
            pushme(f'IPv6地址监控程序异常！{time.strftime("%Y-%m-%d %H:%M:%S")}', f'异常信息：{e}')


if __name__ == '__main__':
    # asyncio.run(async_monitor_ipv6_address_changes())
    now_ipv6 = '2409:8a1e:2e92:5a30'
    latest_ipv6 = '2409:8a1e:2e9a:b040'
    change_ipv6_config(now_ipv6, latest_ipv6)
