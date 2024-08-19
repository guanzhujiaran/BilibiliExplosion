import os

from loguru import logger

from CONFIG import CONFIG

reserve_lot_log = logger.bind(user="预约抽奖")

reserve_lot_log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_reserve_lot_log.log"),
                    level="WARNING",
                    encoding="utf-8",
                    enqueue=True,
                    rotation="500MB",
                    compression="zip",
                    retention="15 days",
                    filter=lambda record: record["extra"].get('user') == "预约抽奖",
                    )
