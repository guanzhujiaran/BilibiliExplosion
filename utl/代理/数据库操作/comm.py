from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab


def get_scheme_ip_port_form_proxy_dict(proxy_info_dict: ProxyTab.proxy) -> str|None:
    if not proxy_info_dict:
        return None
    return list(proxy_info_dict.values())[0]