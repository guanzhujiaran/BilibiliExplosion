import re

from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab


def get_scheme_ip_port_form_proxy_dict(proxy_info_dict: ProxyTab.proxy) -> str|None:
    if not proxy_info_dict:
        return None
    return list(proxy_info_dict.values())[0]

def format_proxy(proxy_str, protocol: str = None) -> dict | None:
    """
    将传入的代理字符串标准化为 {'protocol1': 'address1', 'protocol2': 'address2'} 的形式。

    :param protocol: http https sock4 sock5 socks4 socks5
    :param proxy_str: 代理字符串，可能是IP地址或带有协议前缀的完整URL
    :return: 标准化的代理字典或None（如果输入不符合预期格式）
    """
    ip_pattern = re.compile(r'^(?:(http|https|socks[45]|sock[45])://)?'  # 协议部分（可选）
                            r'((?:[0-9]{1,3}\.){3}[0-9]{1,3})'  # 完整的 IP 地址
                            r'(:[0-9]{2,5})?$'  # 端口号部分（可选）
                            )

    match = ip_pattern.match(proxy_str)
    if not match:
        return None
    protocol_in_input = match.group(1)  # 输入中的协议部分，可能为None
    ip_address = match.group(2)
    port = match.group(3) or ':80'  # 如果没有提供端口，默认使用80
    # 构建基础的代理地址
    base_protocol = protocol_in_input or protocol or 'http'
    # 创建代理字典
    proxy_dict = {}
    if base_protocol in ['http', 'https']:
        proxy_dict['http'] = f'{base_protocol}://{ip_address}{port}'
        proxy_dict['https'] = f'{base_protocol}://{ip_address}{port}'
    elif base_protocol in ['sock5', 'socks5']:
        proxy_dict['sock5'] = f'{base_protocol}://{ip_address}{port}'
        proxy_dict['socks5'] = f'{base_protocol}://{ip_address}{port}'
    elif base_protocol in ['sock4', 'socks4']:
        proxy_dict['sock4'] = f'{base_protocol}://{ip_address}{port}'
        proxy_dict['socks4'] = f'{base_protocol}://{ip_address}{port}'
    else:
        return None
    return proxy_dict
