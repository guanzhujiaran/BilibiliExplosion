import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from enum import StrEnum
import json
import time

from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import ProxyTab
from utl.代理.数据库操作.async_proxy_op_alchemy_mysql_ver import SubRedisStore


# 模拟 RedisManagerBase 的父类行为
class MockRedisManagerBase:
    async def _hlen(self, key):
        return self.hlen.get(key, 0)

    async def _scan(self, cursor=0, match_str="*"):
        return 0, []

    async def _hmset_bulk_batch(self, hm_name, hm_k_v_List):
        pass

    async def _zadd(self, key, mapping):
        pass

    async def _set(self, key, value):
        pass

    async def _get(self, key):
        return None

    async def _hmget(self, name, field):
        return self.hmget_map.get((name, field), None)

    async def _zcard(self, key):
        return 0

    async def _zrand_member(self, key, count=1):
        return []

    async def _zget_top_score(self, key, rand=True):
        return None

    async def _hdel(self, name, field):
        pass

    async def _zdel_elements(self, key, member):
        pass

    async def _delete(self, key):
        pass

    async def _hmset(self, name, field_values):
        pass

    async def _zdel_range(self, key, start, end):
        pass

    async def _del_keys_with_prefix(self, prefix):
        pass


# 构造一个继承自 MockRedisManagerBase 的 SubRedisStore 实现
class TestableSubRedisStore(SubRedisStore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hlen = {}
        self.hmget_map = {}

    async def get_bili_proxy_all_num(self):
        return await super().get_bili_proxy_all_num()

    async def redis_select_one_proxy(self):
        return await super().redis_select_one_proxy()

    async def redis_update_proxy(self, proxy_tab, score_change_num):
        return await super().redis_update_proxy(proxy_tab, score_change_num)


@pytest.fixture
def mock_redis_base():
    store = TestableSubRedisStore()
    store._hlen = AsyncMock(wraps=store._hlen)
    store._hmset_bulk_batch = AsyncMock(wraps=store._hmset_bulk_batch)
    store._zadd = AsyncMock(wraps=store._zadd)
    store._set = AsyncMock(wraps=store._set)
    store._get = AsyncMock(wraps=store._get)
    store._hmget = AsyncMock(wraps=store._hmget)
    store._zcard = AsyncMock(wraps=store._zcard)
    store._zrand_member = AsyncMock(wraps=store._zrand_member)
    store._zget_top_score = AsyncMock(wraps=store._zget_top_score)
    store._hdel = AsyncMock(wraps=store._hdel)
    store._zdel_elements = AsyncMock(wraps=store._zdel_elements)
    store._delete = AsyncMock(wraps=store._delete)
    store._hmset = AsyncMock(wraps=store._hmset)
    store._zdel_range = AsyncMock(wraps=store._zdel_range)
    store._del_keys_with_prefix = AsyncMock(wraps=store._del_keys_with_prefix)
    return store


def create_mock_proxy(ip='127.0.0.1', port=8080, score=5000, status=0):
    proxy = {
        'http': f'http://{ip}:{port}',
        'https': f'https://{ip}:{port}'
    }
    return ProxyTab(proxy=proxy, score=score, status=status)


@pytest.mark.asyncio
async def test_get_bili_proxy_all_num(mock_redis_base):
    mock_redis_base.hlen = {
        mock_redis_base.RedisMap.bili_proxy_available_hm.value: 10,
        mock_redis_base.RedisMap.bili_proxy_black_hm.value: 5
    }

    total = await mock_redis_base.get_bili_proxy_all_num()
    assert total == 15


@pytest.mark.asyncio
async def test_set_sync_ts(mock_redis_base):
    await mock_redis_base.set_sync_ts()
    assert mock_redis_base.sync_ts > 0


@pytest.mark.asyncio
async def test_get_sync_ts(mock_redis_base):
    current_time = int(time.time())
    mock_redis_base.sync_ts = 0
    mock_redis_base._get = AsyncMock(return_value=str(current_time))
    ts = await mock_redis_base.get_sync_ts()
    assert ts == current_time


@pytest.mark.asyncio
async def test_sync_2_redis(mock_redis_base):
    proxy = create_mock_proxy()
    await mock_redis_base.sync_2_redis([proxy])
    mock_redis_base._hmset_bulk_batch.assert_called_once()
    mock_redis_base._zadd.assert_called_once()


@pytest.mark.asyncio
async def test_redis_get_proxy_by_ip(mock_redis_base):
    proxy = create_mock_proxy()
    key, field = mock_redis_base._gen_proxy_key(proxy.proxy)
    mock_redis_base.hmget_map[(key, field)] = json.dumps(proxy.to_dict())

    result = await mock_redis_base.redis_get_proxy_by_ip(proxy.proxy)
    assert result is not None
    assert result.proxy['http'] == proxy.proxy['http']


@pytest.mark.asyncio
async def test_redis_update_proxy(mock_redis_base):
    proxy = create_mock_proxy(score=5000)
    key, field = mock_redis_base._gen_proxy_key(proxy.proxy)
    mock_redis_base.hmget_map[(key, field)] = json.dumps(proxy.to_dict())

    success = await mock_redis_base.redis_update_proxy(proxy, score_change_num=100)
    assert success is not None


@pytest.mark.asyncio
async def test_clear_all_proxy(mock_redis_base):
    await mock_redis_base.redis_clear_all_proxy()
    mock_redis_base.redis_clear_black_proxy.assert_awaited()
    mock_redis_base.redis_clear_changed_proxy.assert_awaited()


@pytest.mark.asyncio
async def test_redis_select_one_proxy(mock_redis_base):
    mock_redis_base._zcard = AsyncMock(return_value=500)
    mock_redis_base._zrand_member = AsyncMock(return_value=["http://192.168.1.201:3128"])
    mock_redis_base.hmget_map[("bili_proxy_available_hm", "http://192.168.1.201:3128")] = '{"proxy": {"http": "http://192.168.1.201:3128"}}'

    proxy = await mock_redis_base.redis_select_one_proxy()
    assert proxy is not None
    assert "http" in proxy.proxy


@pytest.mark.asyncio
async def test_redis_bili_proxy_zset_count(mock_redis_base):
    mock_redis_base._zcard = AsyncMock(return_value=100)
    count = await mock_redis_base.redis_bili_proxy_zset_count()
    assert count == 100


@pytest.mark.asyncio
async def test_redis_get_all_changed_proxy(mock_redis_base):
    mock_redis_base._hgetall = AsyncMock(return_value={"key1": "val1"})
    data = await mock_redis_base.redis_get_all_changed_proxy()
    assert isinstance(data, dict)