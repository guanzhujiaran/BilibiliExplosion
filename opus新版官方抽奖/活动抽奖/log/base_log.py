import os

from loguru import logger

from CONFIG import CONFIG

topic_lot_log = logger.bind(user="话题抽奖")

topic_lot_log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_topic_lot_log.log"),
                    level="WARNING",
                    encoding="utf-8",
                    enqueue=True,
                    rotation="500MB",
                    compression="zip",
                    retention="15 days",
                    filter=lambda record: record["extra"].get('user') == "话题抽奖",
                    )
