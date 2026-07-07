"""
从 t_lotdyninfo.rawJsonStr 重新解析并更新所有字段。

替代原有只回填评论转发数的脚本，本脚本会从 rawJsonStr 中重新提取：
  - 互动数据 (commentCount / repostCount / likeCount)
  - 作者昵称 (authorName)、发布时间 (pubTime)、正文 (dynContent)、链接 (dynamicUrl)
  - 抽奖类型 (officialLotType)：重新判断 官方/充电/预约
  - is_lot：官方抽奖=1，预约/充电=0，其余用 extract_prize_info
  - isManualReply：转为 0/1 (bool)
  - t_lot_extra_info：need_comment / need_repost

用法:
  uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill                          # 使用 .env 默认配置
  uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill --limit 500              # 限制条数

  指定大模型:
  uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill \\
      --llm-base-url https://api.openai.com/v1 \\
      --llm-token sk-xxx \\
      --llm-model gpt-4o

  指定目标数据库:
  uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill \\
      --db-host 192.168.1.200 --db-port 10000 --db-user root --db-password 114514

  仅统计 / 预览:
  uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill --count
  uv run python -m scripts.database.backfill_dyninfo_from_rawjson.backfill --dry-run
"""

import argparse
import asyncio
import datetime
import json
import os
import re
import sys
from typing import Sequence

# 确保项目根目录在 sys.path 中
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from pydantic import BaseModel

from log.base_log import myfastapi_logger
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper
from Service.GetOthersLotDyn.Sql.models import TLotdyninfo
from Service.GetOthersLotDyn.parser.dynamic_detail_parser import parse_dynamic_item
from Service.GetOthersLotDyn.parser.prize_extractor import extract_prize_info
from Service.GetOthersLotDyn.filter.manual_reply_judge import manual_reply_judge
from Models.lottery_database.bili.LotteryDataModels import OfficialLotType
from sqlalchemy import and_, or_, select, update, func

BATCH_SIZE = 50


class ExtraInfoParams(BaseModel):
    """t_lot_extra_info 更新参数"""
    need_comment: int
    need_repost: int


class DynInfoUpdates(BaseModel):
    """t_lotdyninfo 全量更新字段"""
    commentCount: int | None = None
    repostCount: int | None = None
    likeCount: int | None = None
    authorName: str | None = None
    dynContent: str | None = None
    pubTime: datetime.datetime | None = None
    dynamicUrl: str | None = None
    officialLotType: str | None = None
    officialLotId: str | None = None
    isManualReply: int | None = None
    isLot: int | None = None


class BackfillResult(BaseModel):
    """回填结果，包含 dyn_info 更新和 extra_info 参数"""
    dyn_info: DynInfoUpdates
    extra_info: ExtraInfoParams | None = None


def _detect_lottery_type(module_dynamic: dict) -> tuple[bool, bool, bool, str]:
    """从 module_dynamic 中检测抽奖类型，复用 bili_dynamic_item.py 的逻辑。

    :return: (is_official_lot, is_charge_lot, is_reserve_lot, lot_rid)
    """
    is_official_lot = False
    is_charge_lot = False
    is_reserve_lot = False
    lot_rid = ''

    additional = module_dynamic.get('additional')
    if additional:
        upower_lottery = additional.get('upower_lottery')
        if upower_lottery:
            lot_rid = str(upower_lottery.get('rid'))
            is_charge_lot = True
        else:
            reserve = additional.get('reserve')
            if reserve and 'lottery/result' in json.dumps(reserve):
                lot_rid = reserve.get('rid')
                is_reserve_lot = True

    if not is_charge_lot and not is_reserve_lot:
        major = module_dynamic.get('major')
        if major and major.get('type') == 'MAJOR_TYPE_OPUS':
            for nodes in (major.get('opus') or {}).get('summary', {}).get('rich_text_nodes', []) or []:
                if nodes.get('type') == 'RICH_TEXT_NODE_TYPE_LOTTERY':
                    is_official_lot = True
                    lot_rid = str(nodes.get('rid'))
                    break
        if not is_official_lot:
            desc_md = module_dynamic.get('desc')
            if desc_md:
                for nodes in desc_md.get('rich_text_nodes', []) or []:
                    if nodes.get('type') == 'RICH_TEXT_NODE_TYPE_LOTTERY':
                        is_official_lot = True
                        lot_rid = str(nodes.get('rid'))
                        break

    return is_official_lot, is_charge_lot, is_reserve_lot, lot_rid


def _parse_and_build_updates(dyn: TLotdyninfo) -> dict | None:
    """从 rawJsonStr 解析数据，返回需要更新的字段 dict。"""
    raw_json = dyn.rawJsonStr
    if not raw_json:
        return None

    try:
        dynamic_id = str(raw_json.get('id_str', ''))
        if not dynamic_id:
            return None

        wrapped = {'code': 0, 'data': {'item': raw_json}}
        parsed = parse_dynamic_item(dynamic_id, wrapped)
        if not parsed.is_valid():
            return None

        updates: dict = {}

        # 互动数据：只在原值为异常时才更新
        if dyn.commentCount is None or dyn.commentCount < 0:
            if parsed.comment_count is not None and parsed.comment_count >= 0:
                updates['commentCount'] = parsed.comment_count
        if dyn.repostCount is None or dyn.repostCount < 0:
            if parsed.forward_count is not None and parsed.forward_count >= 0:
                updates['repostCount'] = parsed.forward_count
        if dyn.likeCount is None or dyn.likeCount < 0:
            if parsed.like_count is not None and parsed.like_count >= 0:
                updates['likeCount'] = parsed.like_count

        # 作者昵称
        if not dyn.authorName and parsed.author_name:
            updates['authorName'] = parsed.author_name

        # 动态正文
        if not dyn.dynContent and parsed.dynamic_content:
            updates['dynContent'] = parsed.dynamic_content

        # 发布时间
        if not dyn.pubTime and parsed.pub_ts:
            updates['pubTime'] = datetime.datetime.fromtimestamp(parsed.pub_ts)

        # 动态链接
        if not dyn.dynamicUrl:
            updates['dynamicUrl'] = f'https://t.bilibili.com/{dynamic_id}'

        return updates if updates else None
    except Exception as e:
        myfastapi_logger.debug(f'解析 rawJsonStr 失败 dynId={dyn.dynId}: {e}')
        return None


async def _process_and_build_full_updates(dyn: TLotdyninfo) -> BackfillResult | None:
    """从 rawJsonStr 解析并构建全量更新（含 is_lot/isManualReply/officialLotType）。

    :return: BackfillResult 或 None
    """
    raw_json = dyn.rawJsonStr
    if not raw_json:
        return None

    try:
        dynamic_id = str(raw_json.get('id_str', ''))
        if not dynamic_id:
            return None

        wrapped = {'code': 0, 'data': {'item': raw_json}}
        parsed = parse_dynamic_item(dynamic_id, wrapped)
        if not parsed.is_valid():
            return None

        module_dynamic = parsed.module_dynamic or {}
        dynamic_content = parsed.dynamic_content or ''

        # 检测抽奖类型
        is_official_lot, is_charge_lot, is_reserve_lot, lot_rid = _detect_lottery_type(module_dynamic)

        # 官方抽奖类型
        official_lot_type = (
            OfficialLotType.official_lot if is_official_lot
            else OfficialLotType.charge_lot if is_charge_lot
            else OfficialLotType.reserve_lot if is_reserve_lot
            else None
        )

        # prize extract result (一次模型调用提取全部信息)
        prize_result = await extract_prize_info(dyn_content=dynamic_content) if dynamic_content else None
        need_repost = prize_result.result.need_repost if prize_result else False

        # manual_judge (need_comment)
        manual_judge = False
        if dynamic_content:
            manual_judge = await asyncio.to_thread(
                manual_reply_judge.call, 'manual_reply_judge', dynamic_content
            )

        # is_lot 逻辑：官方抽奖=1，预约/充电=0，其余用 extract_prize_info
        if is_official_lot:
            is_lot = True
            need_repost = True
        elif is_reserve_lot or is_charge_lot:
            is_lot = False
        elif prize_result:
            is_lot = prize_result.result.is_lot
            # 评论或转发超多的也算抽奖
            if not is_lot:
                comment_count = parsed.comment_count or 0
                forward_count = parsed.forward_count or 0
                if comment_count > 2000 or forward_count > 1000:
                    is_lot = True
        else:
            is_lot = True

        # 去掉转发 @ 部分
        if re.match(r'.*//@.*', dynamic_content, re.DOTALL) is not None:
            dynamic_content = re.findall(r'(.*?)//@', dynamic_content, re.DOTALL)[0]

        # 动态链接
        ret_url = f'https://t.bilibili.com/{dynamic_id}'
        if need_repost:
            ret_url += '?tab=2'

        dyn_info = DynInfoUpdates(
            commentCount=parsed.comment_count if parsed.comment_count is not None and parsed.comment_count >= 0 else None,
            repostCount=parsed.forward_count if parsed.forward_count is not None and parsed.forward_count >= 0 else None,
            likeCount=parsed.like_count if parsed.like_count is not None and parsed.like_count >= 0 else None,
            authorName=parsed.author_name if parsed.author_name else None,
            dynContent=dynamic_content if dynamic_content else None,
            pubTime=datetime.datetime.fromtimestamp(parsed.pub_ts) if parsed.pub_ts else None,
            dynamicUrl=ret_url,
            officialLotType=official_lot_type.value if official_lot_type else None,
            officialLotId=str(lot_rid) if lot_rid else None,
            isManualReply=int(manual_judge),
            isLot=int(is_lot),
        )

        extra_info = ExtraInfoParams(
            need_comment=int(manual_judge),
            need_repost=int(need_repost),
        )

        return BackfillResult(dyn_info=dyn_info, extra_info=extra_info)
    except Exception as e:
        myfastapi_logger.exception(f'全量解析 rawJsonStr 失败 dynId={dyn.dynId}: {e}')
        return None


async def backfill_dyninfo(limit: int = 0, dry_run: bool = False):
    """主回填流程：从 rawJsonStr 全量更新 t_lotdyninfo 和 t_lot_extra_info。"""
    total_processed = 0
    total_updated = 0
    total_skipped = 0
    field_stats: dict[str, int] = {}

    async def _process_batch(records: Sequence[TLotdyninfo]) -> tuple[int, int, int]:
        nonlocal field_stats
        processed = 0
        updated = 0
        skipped = 0

        async with SqlHelper.async_session() as session:
            for dyn in records:
                processed += 1
                result = await _process_and_build_full_updates(dyn)
                if not result:
                    skipped += 1
                    continue

                updates = result.dyn_info.model_dump(exclude_none=True)

                if dry_run:
                    updated += 1
                    myfastapi_logger.info(
                        f'[DRY-RUN] dynId={dyn.dynId} 将更新字段: {list(updates.keys())}')
                else:
                    stmt = (
                        update(TLotdyninfo)
                        .where(TLotdyninfo.dynId == dyn.dynId)
                        .values(**updates)
                    )
                    await session.execute(stmt)
                    updated += 1

                    # 更新 t_lot_extra_info
                    if result.extra_info:
                        await SqlHelper.save_extra_info(
                            ref_id=dyn.dynId,
                            lot_type="common",
                            need_comment=result.extra_info.need_comment,
                            need_repost=result.extra_info.need_repost,
                        )

                    myfastapi_logger.info(
                        f'已更新 dynId={dyn.dynId} 的字段: {list(updates.keys())}')

                for field in updates:
                    field_stats[field] = field_stats.get(field, 0) + 1

            if not dry_run:
                await session.commit()

        myfastapi_logger.info(
            f'批次完成: 处理 {processed} 条，更新 {updated} 条，跳过 {skipped} 条')
        return processed, updated, skipped

    myfastapi_logger.info('=== 开始全量回填 t_lotdyninfo 数据 ===')
    if dry_run:
        myfastapi_logger.info('*** DRY-RUN 模式，不会实际写入数据库 ***')

    page = 0
    while True:
        async with SqlHelper.async_session() as session:
            stmt = (
                select(TLotdyninfo)
                .filter(TLotdyninfo.rawJsonStr.isnot(None))
                .order_by(TLotdyninfo.dynId.desc())
                .offset(page * BATCH_SIZE)
                .limit(BATCH_SIZE)
            )
            res = await session.execute(stmt)
            records = res.scalars().all()

        if not records:
            myfastapi_logger.info('没有更多需要处理的记录')
            break

        myfastapi_logger.info(f'第 {page + 1} 页查询到 {len(records)} 条待处理记录')

        p, u, s = await _process_batch(records)
        total_processed += p
        total_updated += u
        total_skipped += s

        page += 1

        if limit and total_processed >= limit:
            myfastapi_logger.info(f'已达到处理上限 limit={limit}，停止')
            break

        myfastapi_logger.info(
            f'累计进度: 已处理 {total_processed} 条，更新 {total_updated} 条，跳过 {total_skipped} 条')

    myfastapi_logger.info('=== 回填完成 ===')
    myfastapi_logger.info(f'总处理记录数: {total_processed}')
    myfastapi_logger.info(f'成功更新记录数: {total_updated}')
    myfastapi_logger.info(f'跳过记录数: {total_skipped}')
    myfastapi_logger.info(f'各字段更新次数: {field_stats}')
    if dry_run:
        myfastapi_logger.info('*** 本次为 DRY-RUN，未实际修改数据库 ***')


async def count_has_rawjson() -> int:
    """统计有 rawJsonStr 的记录总数"""
    async with SqlHelper.async_session() as session:
        stmt = (
            select(func.count(TLotdyninfo.dynId))
            .filter(TLotdyninfo.rawJsonStr.isnot(None))
        )
        res = await session.execute(stmt)
        return res.scalar() or 0


async def main():
    parser = argparse.ArgumentParser(
        description='从 t_lotdyninfo.rawJsonStr 全量更新数据（含 is_lot/isManualReply/extra_info）'
    )
    parser.add_argument(
        '--limit', type=int, default=0,
        help='最大处理条数，0 表示不限制 (默认: 0)'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='仅预览需要更新的记录，不实际写入数据库'
    )
    parser.add_argument(
        '--count', action='store_true',
        help='仅统计可回填的记录总数，不做处理'
    )

    from _cli_utils import add_llm_args, add_db_args, apply_cli_overrides
    add_llm_args(parser)
    add_db_args(parser)

    args = parser.parse_args()
    apply_cli_overrides(args)

    if args.count:
        total = await count_has_rawjson()
        myfastapi_logger.info(f'有 rawJsonStr 的记录总数: {total}')
        return

    await backfill_dyninfo(limit=args.limit, dry_run=args.dry_run)


if __name__ == '__main__':
    asyncio.run(main())
