"""
后端 i18n 统一封装（基于 fastapi-i18n，底层为 GNU gettext）。

设计要点：
- `i18n`：FastAPI 依赖，需在应用级 `dependencies=[Depends(i18n)]` 注册，
  每个请求根据 `Accept-Language` 头（或默认语言）初始化翻译环境（ContextVar）。
- `_`：gettext 别名，标记需翻译的原文；**必须在请求上下文中调用**
  （即视图函数 / 依赖函数执行期内），不能在模块或类定义期调用。
- `LOCALE_DIR`：默认指向本包内的 `locale/` 目录（与前端 5 语言一致：
  zh_CN 默认 / en / zh_TW / ja / ko）。

延迟翻译约定：枚举 / 异常类属性在类定义时即求值、无请求上下文，因此这些位置
只能存「原文中文」，在对外返回时（视图/处理器执行期）再调用 `_()` 翻译。
动态字符串（含占位符）：先 `_("模板 {x}")` 再 `.format(x=...)`。
"""

from pathlib import Path

from fastapi_i18n import i18n as _i18n
from fastapi_i18n import _ as _translate

# 默认 locale 目录：bili_common/locale/
DEFAULT_LOCALE_DIR = str(Path(__file__).parent / "locale")

# 对外导出：i18n 依赖 + gettext 别名
i18n = _i18n
_ = _translate

__all__ = ["i18n", "_", "DEFAULT_LOCALE_DIR"]
