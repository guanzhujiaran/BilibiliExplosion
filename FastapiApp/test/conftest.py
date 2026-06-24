import sys
from pathlib import Path

# 将 FastapiApp 目录添加到 Python 路径，使 Service 等模块可以被导入
_fastapi_app_path = Path(__file__).resolve().parent.parent
if str(_fastapi_app_path) not in sys.path:
    sys.path.insert(0, str(_fastapi_app_path))