import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select, delete, and_, or_, case
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from CONFIG import CONFIG
from fastapi接口.log.base_log import sql_log
from fastapi接口.utils.Common import sql_retry_wrapper
from utl.代理.数据库操作.SqlAlcheyObj.ProxyModel import AvailableProxy, ProxyTab


class AvailableProxySqlHelper:
    MIN_USABLE_PROXY_NUM = 50
    MAX_USABLE_PROXY_NUM = 150
    CLEAN_INTERVAL_HOURS = 2

    def __init__(self):
        self.async_egn = create_async_engine(
            CONFIG.database.MYSQL.proxy_db_URI,
            **CONFIG.sql_alchemy_config.engine_config
        )
        self.session = async_sessionmaker(
            self.async_egn,
            **CONFIG.sql_alchemy_config.session_config
        )
        self.log = sql_log
        self.use_good_proxy_flag: bool = False

    @sql_retry_wrapper
    async def get_num(self, is_available: bool = True) -> int:
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        async with self.session() as session:
            try:
                sql = select(func.count(AvailableProxy.pk)).select_from(AvailableProxy).where(
                    AvailableProxy.available == is_available,
                    # --- Usability Criteria Start ---
                    or_(
                        AvailableProxy.counter <= 20,  # Still has low usage count
                        AvailableProxy.max_counter_ts == None,  # Counter never reached max OR was reset
                        AvailableProxy.max_counter_ts < two_hours_ago,  # Max count reached, but cooled down
                        and_(  # Specific handling for response codes if needed
                            AvailableProxy.resp_code == -352,
                            AvailableProxy.latest_352_ts < two_hours_ago
                        ),
                        and_(
                            AvailableProxy.resp_code == -412,
                            AvailableProxy.latest_used_ts < two_hours_ago  # Assuming -412 also needs cooldown
                        )
                    )
                )
                result = await session.execute(sql)
                return result.scalar_one()
            except Exception as e:
                self.log.error(f"Error getting proxy count (available={is_available}): {e}")
                return 0  # Return 0 or raise depending on desired behavior

    @sql_retry_wrapper
    async def del_by_ip(self, ip: str):
        # Be cautious with deleting by IP if IPs are not unique across different proxy_tab entries
        async with self.session() as session:
            async with session.begin():
                try:
                    await session.execute(delete(AvailableProxy).where(AvailableProxy.ip == ip))
                    await session.commit()
                except SQLAlchemyError as e:
                    self.log.error(f"Error deleting proxy by IP {ip}: {e}")
                    await session.rollback()
                    raise  # Or handle differently

    @sql_retry_wrapper
    async def get_rand_available_proxy_sql(self) -> tuple[AvailableProxy | None, int]:
        """
        Attempts to get a random, available, and usable proxy from the database,
        eagerly loading the related ProxyTab.
        Updates the usage counter and timestamps upon successful selection.
        Adjusts the internal flag 'use_good_proxy_flag' based on availability.
        """
        available_num = await self.get_num(is_available=True)
        while 1:
            if available_num > self.MIN_USABLE_PROXY_NUM and self.use_good_proxy_flag:
                now = datetime.now()
                two_hours_ago = now - timedelta(hours=2)
                async with self.session() as session:
                    async with session.begin():
                        stmt = (
                            select(AvailableProxy)
                            .options(selectinload(AvailableProxy.proxy_tab))  # <--- Eager load ProxyTab
                            .where(
                                AvailableProxy.available == True,
                                or_(
                                    AvailableProxy.counter <= 20,
                                    AvailableProxy.max_counter_ts == None,
                                    AvailableProxy.max_counter_ts < two_hours_ago,
                                    and_(AvailableProxy.resp_code == -352,
                                         AvailableProxy.latest_352_ts < two_hours_ago),
                                    and_(AvailableProxy.resp_code == -412,
                                         AvailableProxy.latest_used_ts < two_hours_ago)
                                )
                            )
                            .order_by(func.rand())
                            .limit(1)
                            .with_for_update(skip_locked=True)
                        )
                        result = await session.execute(stmt)
                        proxy_available = result.scalars().first()  # Renamed variable for clarity

                        if proxy_available:
                            # --- Update AvailableProxy stats ---
                            proxy_available.counter += 1
                            proxy_available.latest_used_ts = now

                            if proxy_available.counter > 20 and not proxy_available.max_counter_ts:
                                proxy_available.max_counter_ts = now
                            if proxy_available.counter > 20 and proxy_available.max_counter_ts < two_hours_ago:
                                proxy_available.counter = 1

                            if proxy_available.resp_code == -352 and proxy_available.latest_352_ts < two_hours_ago:
                                proxy_available.resp_code = 0
                            # --- Check if ProxyTab was loaded ---
                            if not proxy_available.proxy_tab:
                                return None, available_num  # Treat as failure
                            return proxy_available, available_num  # Return the AvailableProxy object (caller will access .proxy_tab)
                        else:
                            return None, available_num
            else:
                if available_num > self.MAX_USABLE_PROXY_NUM:
                    self.use_good_proxy_flag = True
                    continue
                if available_num < self.MIN_USABLE_PROXY_NUM:
                    self.use_good_proxy_flag = False
                return None, available_num

    # --- Keep existing methods ---
    @sql_retry_wrapper
    async def get_available_proxy_by_proxy_id(self, proxy_tab_id: int) -> Optional[AvailableProxy]:
        async with self.session() as session:
            try:
                result = await session.execute(
                    select(AvailableProxy)
                    .where(
                        AvailableProxy.proxy_tab_id == proxy_tab_id,
                    )
                    .limit(1)
                )
                return result.scalars().first()
            except SQLAlchemyError as e:
                self.log.error(f"Error getting proxy by tab id {proxy_tab_id}: {e}")
                return None

    @sql_retry_wrapper
    async def update_proxy_counter_and_time(self, proxy_pk: int):
        # This method seems redundant if get_rand_available_proxy_sql handles updates
        # But keeping it if used elsewhere
        async with self.session() as session:
            async with session.begin():
                try:
                    proxy = await session.get(AvailableProxy, proxy_pk)
                    if not proxy:
                        self.log.warning(f"Proxy pk={proxy_pk} not found for counter update.")
                        return

                    original_counter = proxy.counter
                    proxy.counter += 1
                    proxy.latest_used_ts = datetime.now()

                    if original_counter == 20:  # Just crossed the threshold
                        proxy.max_counter_ts = datetime.now()
                    elif proxy.counter > 20 and proxy.max_counter_ts is None:  # Safety check
                        proxy.max_counter_ts = datetime.now()

                    # Commit handled by context manager
                except SQLAlchemyError as e:
                    self.log.error(f"Error updating counter for proxy pk={proxy_pk}: {e}")
                    # Rollback handled by context manager
                    raise  # Or handle differently

    @sql_retry_wrapper
    async def delete_proxy_by_pk(self, proxy_pk: int):
        async with self.session() as session:
            async with session.begin():
                try:
                    stmt = delete(AvailableProxy).where(AvailableProxy.pk == proxy_pk)
                    result = await session.execute(stmt)
                    if result.rowcount == 0:
                        self.log.warning(f"Attempted to delete proxy pk={proxy_pk}, but it was not found.")
                    # Commit handled by context manager
                except SQLAlchemyError as e:
                    self.log.error(f"Error deleting proxy pk={proxy_pk}: {e}")
                    # Rollback handled by context manager
                    raise  # Or handle differently

    @sql_retry_wrapper
    async def update_proxy_resp_code(self, proxy_pk: int, resp_code: int):
        async with self.session() as session:
            async with session.begin():
                try:
                    proxy = await session.get(AvailableProxy, proxy_pk)
                    if not proxy:
                        self.log.warning(f"Proxy pk={proxy_pk} not found for resp_code update.")
                        return

                    now = datetime.now()
                    proxy.resp_code = resp_code
                    proxy.latest_used_ts = now  # Always update latest used time

                    if resp_code == -352:
                        proxy.latest_352_ts = now
                    # Add logic for other specific codes if needed
                    # e.g., if resp_code indicates proxy is dead:
                    # if resp_code in [DEAD_CODE_1, DEAD_CODE_2]:
                    #    proxy.available = False

                    # Commit handled by context manager
                except SQLAlchemyError as e:
                    self.log.error(f"Error updating resp_code for proxy pk={proxy_pk}: {e}")
                    # Rollback handled by context manager
                    raise  # Or handle differently

    # @sql_retry_wrapper
    async def update_available_proxy_details(self, proxy_tab: ProxyTab, available: bool, resp_code: int):
        """
        Updates specific fields (available, resp_code, timestamps) of an AvailableProxy record
        identified by its associated proxy_tab_id.
        If the record does not exist and `available` is True, a new record is inserted.
        If the record does not exist and `available` is False, no action is taken.
        """
        try:
            proxy_id = proxy_tab.proxy_id
            computed_proxy_str = proxy_tab.computed_proxy_str
            now = datetime.now()
            latest_352_ts = now if resp_code == -352 else None
            new_values = {
                "ip": computed_proxy_str,
                "available": available,
                "resp_code": resp_code,
                "counter": AvailableProxy.counter if not available else 1,  # Increment counter
                "latest_used_ts": now,
                "max_counter_ts": case(
                    (AvailableProxy.counter >= 30, now),  # Example condition to update max_counter_ts
                    else_=AvailableProxy.max_counter_ts
                ),
                "latest_352_ts": latest_352_ts
            }

            async with self.session() as session:
                stmt = mysql_insert(AvailableProxy).values(
                    proxy_tab_id=proxy_id,
                    **new_values
                )

                # On duplicate key update specified fields
                update_stmt = stmt.on_duplicate_key_update(**new_values)

                result = await session.execute(update_stmt)
                await session.commit()

                return result
        except Exception as e:
            self.log.error(f"Error updating available proxy details for proxy_id={proxy_tab}: {e}")

sql_helper = AvailableProxySqlHelper()
if __name__ == "__main__":
    async def _test_update_available_proxy_details():
        await sql_helper.update_available_proxy_details(
            ProxyTab(
                proxy_id=2588172,
                proxy="{'http':'http://192.168.1.201:3128','https':'http://192.168.1.201:3128'}",
                status=0,
                update_ts=int(time.time()),
                score=1,
                add_ts=int(time.time()),
                success_times=1,
                zhihu_status=0,
                computed_proxy_str='https://111.200.255.18:7081'
            ),
            True,
            0
        )


    print(asyncio.run(_test_update_available_proxy_details()))
