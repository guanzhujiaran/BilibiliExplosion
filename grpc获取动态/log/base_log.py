import os
from loguru import logger
from CONFIG import CONFIG

grpc_api_any_log = logger.bind(user="GrpcAnyElse")
grpc_api_any_log.add(os.path.join(CONFIG.root_dir, "fastapi接口/scripts/log/error_grpc_api_log.log"),
                     level="ERROR",
                     encoding="utf-8",
                     enqueue=True,
                     rotation="500MB",
                     compression="zip",
                     retention="15 days",
                     filter=lambda record: record["extra"].get('user') == "GrpcAnyElse",
                     )
