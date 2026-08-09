"""deps: 依赖注入函数（FastAPI Header 等）

各依赖（get_auth_info_from_header / require_root / require_admin / require_permission 等）
请从 `bili_common.deps.auth` 直接导入；本包 `__init__` 保持精简以避免循环依赖。
"""
