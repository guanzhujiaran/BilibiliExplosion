import os

from loguru import logger

from CONFIG import CONFIG

official_lot_log = logger.bind(user="官方抽奖")

official_lot_log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_official_lot_log.log"),
                    level="WARNING",
                    encoding="utf-8",
                    enqueue=True,
                    rotation="500MB",
                    compression="zip",
                    retention="15 days",
                    filter=lambda record: record["extra"].get('user') == "官方抽奖",
                    )
