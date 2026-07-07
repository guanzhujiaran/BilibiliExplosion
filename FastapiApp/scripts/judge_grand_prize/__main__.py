#!/usr/bin/env python3
"""
手动执行脚本：对所有已入库的抽奖数据使用 LLM 进行大奖判断，并将结果写入子表。

使用方式:
    cd FastapiApp
    uv run python -m scripts.judge_grand_prize                            # 判断全部类型 (.env 默认配置)
    uv run python -m scripts.judge_grand_prize --type common              # 仅判断普通抽奖
    uv run python -m scripts.judge_grand_prize --type reserve             # 仅判断预约抽奖
    uv run python -m scripts.judge_grand_prize --type official            # 仅判断官方/充电抽奖
    uv run python -m scripts.judge_grand_prize --force-update             # 强制重新判断所有

指定大模型 (有 GPU 的机器):
    uv run python -m scripts.judge_grand_prize \\
        --llm-base-url https://api.openai.com/v1 \\
        --llm-token sk-xxx \\
        --llm-model gpt-4o

指定目标数据库:
    uv run python -m scripts.judge_grand_prize \\
        --db-host 192.168.1.200 --db-port 10000 --db-user root

可选参数:
    --type all|common|reserve|official  抽奖类型 (默认: all=全部)
    --batch-size 200                    每批处理数量 (默认: 200)
    --dry-run                           仅打印将要处理的数量，不实际写入
    --force-update                      强制重新判断所有记录（即使已有flag）
    --limit N                           限制最大处理数量，0=不限制 (默认: 0)
    --llm-base-url                      大模型 API 地址 (覆盖 .env)
    --llm-token                         大模型 API token (覆盖 .env)
    --llm-model                         模型名称 (覆盖 .env)
    --db-host                           MySQL 主机 (覆盖 .env)
    --db-port                           MySQL 端口 (覆盖 .env)
    --db-user                           MySQL 用户名 (覆盖 .env)
    --db-password                       MySQL 密码 (覆盖 .env)

注意:
    - 所有抽奖类型的大奖判断结果均写入独立子表 t_lot_extra_info
    - 普通抽奖使用 (ref_id=dynId, lot_type='common')
    - 预约抽奖使用 (ref_id=ids, lot_type='reserve')
    - 官方/充电抽奖使用 (business_id, 通过 Grpc SQLHelper)
    - 基于 Qwen3.5-0.8B + vLLM 推理，替代原有 SVM 模型
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# 确保项目根目录在 sys.path 中
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))





def _format_stats(stats: dict, title: str, total_elapsed: float) -> None:
    """统一格式化输出统计信息"""
    print("-" * 60)
    print(f"处理完成! [{title}] 总耗时: {total_elapsed:.1f}s")
    print(f"  总记录数: {stats['total_records']}")
    print(f"  已处理:   {stats['processed']}")
    print(f"  大奖:     {stats['grand_prize']}")
    print(f"  非大奖:   {stats['not_grand_prize']}")
    print(f"  跳过:     {stats['skipped']}")
    print(f"  错误:     {stats['errors']}")


async def judge_common_lottery(
    batch_size: int = 200,
    dry_run: bool = False,
    force_update: bool = False,
    limit: int = 0,
) -> dict:
    """
    对所有普通抽奖动态 (TLotdyninfo) 执行 LLM 大奖判断并写入 t_lot_extra_info。

    返回统计信息。
    """
    from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper
    from Service.GetOthersLotDyn.parser.prize_extractor import extract_prize_info

    stats = {
        "total_records": 0,
        "processed": 0,
        "grand_prize": 0,
        "not_grand_prize": 0,
        "skipped": 0,
        "errors": 0,
    }

    print("=" * 60)
    print("开始对普通抽奖动态执行 LLM 大奖判断")
    print(f"  每批数量: {batch_size}")
    print(f"  Dry-Run: {dry_run}")
    print(f"  强制更新: {force_update}")
    print(f"  最大数量: {'无限制' if limit == 0 else limit}")
    print("=" * 60)

    if force_update:
        dyn_ids = await SqlHelper.get_all_common_lot_dyn_ids(limit=limit)
    else:
        dyn_ids = await SqlHelper.get_ref_ids_without_extra_info(
            lot_type="common", limit=limit
        )

    stats["total_records"] = len(dyn_ids)

    if not dyn_ids:
        print("没有找到需要判断的记录。")
        return stats

    print(f"共找到 {len(dyn_ids)} 条需要判断的记录")

    if dry_run:
        print(f"[Dry-Run] 将处理 {len(dyn_ids)} 条记录，不实际写入数据库。")
        return stats

    total_batches = (len(dyn_ids) + batch_size - 1) // batch_size
    start_time = time.time()

    for batch_idx in range(0, len(dyn_ids), batch_size):
        batch = dyn_ids[batch_idx : batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        batch_start = time.time()

        content_map = await SqlHelper.get_dyn_info_batch(batch)

        if not content_map:
            print(f"  [批次 {batch_num}/{total_batches}] 无有效内容，跳过")
            continue

        batch_items = [(dyn_id, content_map[dyn_id]) for dyn_id in batch if dyn_id in content_map]
        if not batch_items:
            print(f"  [批次 {batch_num}/{total_batches}] 内容均为空，跳过")
            continue

        for dyn_id, content in batch_items:
            try:
                result = await extract_prize_info(dyn_content=content)
                is_grand = int(result.result.is_grand_prize)
                await SqlHelper.save_extra_info(
                    ref_id=dyn_id,
                    lot_type="common",
                    is_grand_prize=is_grand,
                )
                stats["processed"] += 1
                if is_grand == 1:
                    stats["grand_prize"] += 1
                else:
                    stats["not_grand_prize"] += 1
            except Exception as e:
                print(f"  [批次 {batch_num}] dynId={dyn_id} 失败: {e}")
                stats["errors"] += 1

        batch_elapsed = time.time() - batch_start
        total_elapsed = time.time() - start_time
        progress = min(batch_idx + batch_size, len(dyn_ids))
        pct = progress / len(dyn_ids) * 100

        print(
            f"  [批次 {batch_num}/{total_batches}] "
            f"处理 {len(batch_items)} 条 | 进度 {pct:.1f}% | "
            f"本批 {batch_elapsed:.1f}s | 累计 {total_elapsed:.1f}s"
        )

    total_elapsed = time.time() - start_time
    _format_stats(stats, "普通抽奖动态", total_elapsed)

    return stats


async def judge_reserve_lottery(
    batch_size: int = 200,
    dry_run: bool = False,
    force_update: bool = False,
    limit: int = 0,
) -> dict:
    """
    对所有预约抽奖 (t_up_reserve_relation_info) 执行 LLM 大奖判断，
    结果写入 t_lot_extra_info (lot_type='reserve')。

    返回统计信息。
    """
    from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper
    from Service.GetOthersLotDyn.parser.prize_extractor import extract_prize_info
    from Service.opus新版官方抽奖.预约抽奖.db.sqlHelper import bili_reserve_sqlhelper

    stats = {
        "total_records": 0,
        "processed": 0,
        "grand_prize": 0,
        "not_grand_prize": 0,
        "skipped": 0,
        "errors": 0,
    }

    print("=" * 60)
    print("开始对预约抽奖执行 LLM 大奖判断")
    print("  结果写入: t_lot_extra_info (lot_type=reserve)")
    print(f"  每批数量: {batch_size}")
    print(f"  Dry-Run: {dry_run}")
    print(f"  强制更新: {force_update}")
    print(f"  最大数量: {'无限制' if limit == 0 else limit}")
    print("=" * 60)

    all_records = await bili_reserve_sqlhelper.get_all_reserve_lottery()

    if not all_records:
        print("没有找到预约抽奖记录。")
        return stats

    all_records = [r for r in all_records if r.text]

    if not force_update:
        all_ids = [r.ids for r in all_records]
        existing_flags = await SqlHelper.get_extra_info_by_ref_ids(
            all_ids, lot_type="reserve"
        )
        target_records = [r for r in all_records if r.ids not in existing_flags]
        stats["skipped"] = len(all_records) - len(target_records)
    else:
        target_records = all_records

    if limit > 0:
        target_records = target_records[:limit]

    stats["total_records"] = len(target_records)

    print(f"共找到 {len(target_records)} 条需要判断的记录 "
          f"(总记录数: {len(all_records)}, 已跳过: {stats['skipped']})")

    if not target_records:
        print("没有需要判断的记录。")
        return stats

    if dry_run:
        print(f"[Dry-Run] 将处理 {len(target_records)} 条记录，不实际写入数据库。")
        return stats

    total_batches = (len(target_records) + batch_size - 1) // batch_size
    start_time = time.time()

    for batch_idx in range(0, len(target_records), batch_size):
        batch = target_records[batch_idx : batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        batch_start = time.time()

        for record in batch:
            try:
                result = await extract_prize_info(dyn_content=record.text)
                is_grand = int(result.result.is_grand_prize)
                await SqlHelper.save_extra_info(
                    ref_id=record.ids,
                    lot_type="reserve",
                    is_grand_prize=is_grand,
                )
                stats["processed"] += 1
                if is_grand == 1:
                    stats["grand_prize"] += 1
                else:
                    stats["not_grand_prize"] += 1
            except Exception as e:
                print(f"  [批次 {batch_num}] ids={record.ids} 失败: {e}")
                stats["errors"] += 1

        batch_elapsed = time.time() - batch_start
        total_elapsed = time.time() - start_time
        progress = min(batch_idx + batch_size, len(target_records))
        pct = progress / len(target_records) * 100

        print(
            f"  [批次 {batch_num}/{total_batches}] "
            f"处理 {len(batch)} 条 | 进度 {pct:.1f}% | "
            f"本批 {batch_elapsed:.1f}s | 累计 {total_elapsed:.1f}s"
        )

    total_elapsed = time.time() - start_time
    _format_stats(stats, "预约抽奖", total_elapsed)

    return stats


async def judge_official_lottery(
    batch_size: int = 200,
    dry_run: bool = False,
    force_update: bool = False,
    limit: int = 0,
) -> dict:
    """
    对所有官方/充电抽奖 (lotdata 表) 执行 LLM 大奖判断，
    结果写入 t_lot_extra_info (通过 lottery_id 关联)。

    返回统计信息。
    """
    from Service.GetOthersLotDyn.parser.prize_extractor import extract_prize_info_for_dyndetail
    from Service.GrpcModule.GrpcSrc.SQLObject.DynDetailSqlHelperMysqlVer import (
        grpc_sql_helper,
    )

    stats = {
        "total_records": 0,
        "processed": 0,
        "grand_prize": 0,
        "not_grand_prize": 0,
        "skipped": 0,
        "errors": 0,
    }

    print("=" * 60)
    print("开始对官方/充电抽奖 (lotdata) 执行 LLM 大奖判断")
    print("  结果写入: t_lot_extra_info (via lottery_id)")
    print(f"  每批数量: {batch_size}")
    print(f"  Dry-Run: {dry_run}")
    print(f"  强制更新: {force_update}")
    print(f"  最大数量: {'无限制' if limit == 0 else limit}")
    print("=" * 60)

    all_records = await grpc_sql_helper.query_all_lottery_data()

    if not all_records:
        print("没有找到 lotdata 记录。")
        return stats

    record_map: dict[int, tuple] = {}
    skipped_no_bid = 0
    skipped_no_text = 0
    for r in all_records:
        if not r.business_id:
            skipped_no_bid += 1
            continue
        prize_cmts = [r.first_prize_cmt, r.second_prize_cmt, r.third_prize_cmt]
        lottery_text = " ".join(filter(lambda a: a, prize_cmts)).strip()
        if not lottery_text:
            skipped_no_text += 1
            continue
        record_map[r.lottery_id] = (lottery_text, r)

    print(f"总 lotdata 记录数: {len(all_records)}")
    print(f"  无 business_id 跳过: {skipped_no_bid}")
    print(f"  无奖品描述跳过:     {skipped_no_text}")
    print(f"  有效记录数:          {len(record_map)}")

    if not record_map:
        print("没有有效的 lotdata 记录可供判断。")
        return stats

    target_ids = list(record_map.keys())
    if not force_update:
        existing_ids = await grpc_sql_helper.batch_check_existing_extra_info(
            target_ids
        )
        target_ids = [bid for bid in target_ids if bid not in existing_ids]
        stats["skipped"] = len(record_map) - len(target_ids)

    if limit > 0:
        target_ids = target_ids[:limit]

    stats["total_records"] = len(target_ids)

    print(f"共找到 {len(target_ids)} 条需要判断的记录 "
          f"(有效总数: {len(record_map)}, 已跳过: {stats['skipped']})")

    if not target_ids:
        print("没有需要判断的记录。")
        return stats

    if dry_run:
        print(f"[Dry-Run] 将处理 {len(target_ids)} 条记录，不实际写入数据库。")
        return stats

    total_batches = (len(target_ids) + batch_size - 1) // batch_size
    start_time = time.time()

    for batch_idx in range(0, len(target_ids), batch_size):
        batch_ids = target_ids[batch_idx : batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        batch_start = time.time()

        flags: dict[int, int] = {}
        for bid in batch_ids:
            try:
                lottery_text = record_map[bid][0]
                result = await extract_prize_info_for_dyndetail(dyn_content=lottery_text)
                is_grand = int(result.result.is_grand_prize)
                flags[bid] = is_grand
                if is_grand == 1:
                    stats["grand_prize"] += 1
                else:
                    stats["not_grand_prize"] += 1
                stats["processed"] += 1
            except Exception as e:
                print(f"  [批次 {batch_num}] lottery_id={bid} 失败: {e}")
                stats["errors"] += 1

        if flags:
            try:
                await grpc_sql_helper.batch_save_extra_info(flags)
            except Exception as e:
                print(f"  [批次 {batch_num}] 批量写入失败: {e}")
                stats["errors"] += len(flags)
                stats["processed"] -= len(flags)
                grand_count = sum(1 for v in flags.values() if v == 1)
                stats["grand_prize"] -= grand_count
                stats["not_grand_prize"] -= len(flags) - grand_count

        batch_elapsed = time.time() - batch_start
        total_elapsed = time.time() - start_time
        progress = min(batch_idx + batch_size, len(target_ids))
        pct = progress / len(target_ids) * 100

        print(
            f"  [批次 {batch_num}/{total_batches}] "
            f"处理 {len(batch_ids)} 条 | 进度 {pct:.1f}% | "
            f"本批 {batch_elapsed:.1f}s | 累计 {total_elapsed:.1f}s"
        )

    total_elapsed = time.time() - start_time
    _format_stats(stats, "官方/充电抽奖", total_elapsed)

    return stats


async def main():
    parser = argparse.ArgumentParser(
        description="对所有已入库的抽奖数据使用 LLM 进行大奖判断并写入子表"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="all",
        choices=["all", "common", "reserve", "official"],
        help="抽奖类型: all=全部, common=普通抽奖动态, reserve=预约抽奖, official=官方/充电抽奖 (默认: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="每批处理数量 (默认: 200)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印将要处理的数量，不实际写入数据库",
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="强制重新判断所有记录（即使已有 flag 记录）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="限制最大处理数量，0=不限制 (默认: 0)"
    )

    from scripts._cli_utils import add_llm_args, add_db_args, apply_cli_overrides
    add_llm_args(parser)
    add_db_args(parser)

    args = parser.parse_args()
    apply_cli_overrides(args)

    if args.type in ("all", "common"):
        await judge_common_lottery(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            force_update=args.force_update,
            limit=args.limit,
        )
    if args.type in ("all", "reserve"):
        await judge_reserve_lottery(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            force_update=args.force_update,
            limit=args.limit,
        )
    if args.type in ("all", "official"):
        await judge_official_lottery(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            force_update=args.force_update,
            limit=args.limit,
        )


if __name__ == "__main__":
    asyncio.run(main())