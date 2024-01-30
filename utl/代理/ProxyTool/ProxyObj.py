# 存放代理对象
import time
from dataclasses import dataclass
from typing import Union, TypedDict


@dataclass
class MyProxyData:
    """
    从dict里面初始化的时候使用MyProxyData(**a)命令，解压dict后自动赋值
    """
    proxy_id: int
    proxy: dict
    status: int
    update_ts: int
    score: int
    add_ts: int
    success_times: int
    zhihu_status: int

    counter: int = 0  # 使用次数
    max_counter_ts: int = 0  # 达到最大的时间戳
    code: int = 0  # 返回响应的代码。0或者-352

    def __dict__(self)->dict:
        """
        返回数据库里面的格式，而不是自带的内容
        :return:
        """
        return {'proxy_id': self.proxy_id,
                'proxy': self.proxy,
                'status': self.status,
                'update_ts': self.update_ts,
                'score': self.score,
                'add_ts': self.add_ts,
                'success_times': self.success_times,
                'zhihu_status': self.zhihu_status
                }

    def is_available(self,is_using=False) -> bool:
        '''
        检查是否可用，如果正在使用则使用次数自动加1
        :return:
        '''
        if int(time.time()) - self.max_counter_ts >= 3600:  # 如果一小时以上就重置为0
            self.counter = 1
            self.code = 0
            self.max_counter_ts = int(time.time())
            return True
        if self.code == -352:
            return False
        if self.counter >= 200:
            self.code = -352
            self.max_counter_ts = int(time.time())
            return False
        if is_using:
            self.counter += 1
        return True


class MyProxyDataTools:
    @staticmethod
    def delete_from_list(myProxyData, MyProxyDataList: list[MyProxyData]):
        res = list(filter(lambda x: x.proxy == myProxyData.proxy, MyProxyDataList))
        if res:
            MyProxyDataList.remove(res[0])

    @staticmethod
    def update_from_list(myProxyData, MyProxyDataList: list[MyProxyData]):
        res = list(filter(lambda x: x.proxy == myProxyData.proxy, MyProxyDataList))
        if res:
            temp = res[0]
            temp.proxy = myProxyData.proxy
            temp.status = myProxyData.status
            temp.update_ts = myProxyData.update_ts
            temp.score = myProxyData.score
            temp.add_ts = myProxyData.add_ts
            temp.success_times = myProxyData.success_times
            temp.zhihu_status = myProxyData.zhihu_status

    @staticmethod
    def get_MyProxyData_by_proxy_dict(proxy_dict, MyProxyDataList: list[MyProxyData]) -> Union[MyProxyData, None]:
        """

        :param proxy_dict: {http:'http://127.0.0.1:1234',https:'http://127.0.0.1:1234'}
        :param MyProxyDataList:
        :return:
        """
        res = list(filter(lambda x: x.proxy == proxy_dict, MyProxyDataList))
        if res:
            return res[0]
        else:
            return None


class TypePDict(TypedDict):
    '''
    写注释用的class
    '''
    proxy_id: int
    proxy: dict
    status: int
    update_ts: int
    score: int
    add_ts: int
    success_times: int
    zhihu_status: int