import os

from loguru import logger

from CONFIG import CONFIG

bapi_log = logger.bind(user="BAPI日志")

bapi_log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_BAPI_log.log"),
                    level="WARNING",
                    encoding="utf-8",
                    enqueue=True,
                    rotation="500MB",
                    compression="zip",
                    retention="15 days",
                    filter=lambda record: record["extra"].get('user') == "BAPI日志",
                    )
