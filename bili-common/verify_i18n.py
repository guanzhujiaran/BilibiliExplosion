"""验证 fastapi-i18n 随 Accept-Language 切换翻译（开发期验证，可删除）。"""
import os
import asyncio
from contextlib import asynccontextmanager

os.environ["FASTAPI_I18N__LOCALE_DIR"] = os.path.abspath("bili_common/locale")
os.environ["FASTAPI_I18N__LOCALE_DEFAULT"] = "zh_CN"

import fastapi_i18n
from fastapi_i18n import i18n, _

from bili_common.models.response_msg import ResponseMsg
from bili_common.exceptions import NotLoggedInException, InvalidUIDException


async def run_with(lang_header: str, label: str):
    # 进入 i18n 依赖（模拟请求级语言设置）
    gen = i18n(accept_language=lang_header)
    await gen.__anext__()
    try:
        print(f"\n=== Accept-Language: {lang_header} ({label}) ===")
        # 1. 直接 _() 字面量
        print("  _('请求参数校验失败') ->", _( "请求参数校验失败"))
        print("  _('权限不足')          ->", _( "权限不足"))
        # 2. ResponseMsg 延迟翻译
        print("  ResponseMsg.not_logged_in.t() ->", ResponseMsg.exception_not_logged_in.t())
        print("  ResponseMsg.fp_limit.t(max=3) ->",
              ResponseMsg.exception_fingerprint_limit_exceeded.t(max=3))
        # 3. 异常 to_response（含 _(self.msg)）
        exc = NotLoggedInException()
        print("  NotLoggedInException.to_response() ->", exc.to_response())
        exc2 = InvalidUIDException(uid="abc123")
        print("  InvalidUIDException(uid).detail ->", exc2.detail)
    finally:
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass


async def main():
    await run_with("zh_CN", "简体")
    await run_with("en", "English")
    await run_with("ja", "日本語")
    await run_with("ko", "한국어")
    await run_with("zh_TW", "繁體")


if __name__ == "__main__":
    asyncio.run(main())
