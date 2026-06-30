#!/usr/bin/env python3
"""
手动执行脚本：对所有已入库的抽奖数据进行 SVM 大奖判断，并将结果写入 t_lot_grand_prize_flag 子表。

使用方式:
    cd FastapiApp
    python scripts/judge_all_grand_prize_flags.py

可选参数:
    --type common      仅判断普通抽奖动态 (默认: common)
    --batch-size 200  每批处理数量 (默认: 200)
    --dry-run          仅打印将要处理的数量，不实际写入
    --force-update     强制重新判断所有记录（即使已有flag）

注意:
    - 此脚本不修改原有表结构，仅写入新增的 t_lot_grand_prize_flag 子表
    - SVM 模型文件需存在于 Service/GetOthersLotDyn/svmJudgeBigLot/ 和
      Service/GetOthersLotDyn/svmJudgeBigReserve/ 目录下
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# 确保项目根目录在 sys.path 中
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from Service.GetOthersLotDyn.Sql.models import TLotGrandPrizeFlag
from Service.GetOthersLotDyn.Sql.sql_helper import SqlHelper


async def judge_common_lottery(
    batch_size: int = 200,
    dry_run: bool = False,
    force_update: bool = False,
) -> dict:
    """
    对所有普通抽奖动态 (TLotdyninfo) 执行 SVM 大奖判断并写入 t_lot_grand_prize_flag。

    返回统计信息。
    """
    from Service.GetOthersLotDyn.svmJudgeBigLot.judgeBigLot import big_lot_predict

    stats = {
        "total_records": 0,
        "processed": 0,
        "grand_prize": 0,
        "not_grand_prize": 0,
        "skipped": 0,
        "errors": 0,
    }

    print("=" * 60)
    print("开始对普通抽奖动态执行 SVM 大奖判断")
    print(f"  每批数量: {batch_size}")
    print(f"  Dry-Run: {dry_run}")
    print(f"  强制更新: {force_update}")
    print("=" * 60)

    # 获取所有需要判断的 dynId
    if force_update:
        dyn_ids = await SqlHelper.get_all_common_lot_dyn_ids(limit=100000)
    else:
        dyn_ids = await SqlHelper.get_ref_ids_without_grand_prize_flag(
            lot_type="common", limit=100000
        )

    stats["total_records"] = len(dyn_ids)

    if not dyn_ids:
        print("没有找到需要判断的记录。")
        return stats

    print(f"共找到 {len(dyn_ids)} 条需要判断的记录")

    if dry_run:
        print(f"[Dry-Run] 将处理 {len(dyn_ids)} 条记录，不实际写入数据库。")
        return stats

    # 分批处理
    total_batches = (len(dyn_ids) + batch_size - 1) // batch_size
    start_time = time.time()

    for batch_idx in range(0, len(dyn_ids), batch_size):
        batch = dyn_ids[batch_idx : batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        batch_start = time.time()

        # 批量获取动态内容
        content_map = await SqlHelper.get_dyn_info_batch(batch)

        if not content_map:
            print(f"  [批次 {batch_num}/{total_batches}] 无有效内容，跳过")
            continue

        # 提取内容列表（保持与 dyn_id 的对应关系）
        batch_items = [(dyn_id, content_map[dyn_id]) for dyn_id in batch if dyn_id in content_map]
        if not batch_items:
            print(f"  [批次 {batch_num}/{total_batches}] 内容均为空，跳过")
            continue

        dyn_ids_batch = [item[0] for item in batch_items]
        contents = [item[1] for item in batch_items]

        # 运行 SVM 判断
        try:
            predictions = await big_lot_predict(contents)
        except Exception as e:
            print(f"  [批次 {batch_num}/{total_batches}] SVM 预测失败: {e}")
            stats["errors"] += len(batch_items)
            continue

        # 批量写入结果
        for i, (dyn_id, _) in enumerate(batch_items):
            is_grand = int(predictions[i]) if i < len(predictions) else 0
            try:
                await SqlHelper.save_grand_prize_flag(
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
                print(f"  [批次 {batch_num}] 写入 dynId={dyn_id} 失败: {e}")
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
    print("-" * 60)
    print(f"处理完成! 总耗时: {total_elapsed:.1f}s")
    print(f"  总记录数: {stats['total_records']}")
    print(f"  已处理:   {stats['processed']}")
    print(f"  大奖:     {stats['grand_prize']}")
    print(f"  非大奖:   {stats['not_grand_prize']}")
    print(f"  跳过:     {stats['skipped']}")
    print(f"  错误:     {stats['errors']}")

    return stats


async def main():
    parser = argparse.ArgumentParser(
        description="对所有已入库的抽奖数据进行 SVM 大奖判断并写入子表"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="common",
        choices=["common"],
        help="抽奖类型 (默认: common=普通抽奖动态)",
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
    args = parser.parse_args()

    if args.type == "common":
        await judge_common_lottery(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            force_update=args.force_update,
        )
    else:
        print(f"不支持的抽奖类型: {args.type}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
