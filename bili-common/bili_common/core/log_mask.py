"""日志脱敏与「响应体摘要」的统一实现（crawler / message-service 共用）。

背景（线上问题）：

- 推送渠道德降级日志把 ``body={data}`` 整个打进 ERROR，``push_key`` /
  ``push_plus_token`` 明文落盘；
- 动态详情 / 空间动态的解析失败日志把**整个响应体**拼进消息，既打爆日志体积，
  又顺带泄露 cookie、设备指纹等线索；
- 异常信息被超长响应体挤到日志末尾，真正的原因反而看不见。

约定：

- 任何要落盘的「可能是密钥的文本 / 字典」都先过 :func:`mask_secret`；
- ERROR 级别只记 ``code`` / ``message`` / 关键 id（见 :func:`response_brief`），
  完整响应在 ``LOG_FULL_RESPONSE=true`` 时才可以输出（见 :func:`full_response_log_enabled`）。
"""

import json
import os
import re
from collections.abc import Mapping
from typing import Any

#: 打码后的占位符（不保留任何明文字符，避免「打一半」被猜出后半段）
MASK = "****"

#: 字段名（大小写不敏感）命中任一关键字即整体打码。
#: 刻意**不**收录过宽的 ``key``：``proxy_key`` / ``msg_id`` 这类是排查必需的非敏感值。
SECRET_FIELD_KEYWORDS: tuple[str, ...] = (
    "push_key",
    "push_plus_token",
    "pushplus_token",
    "bearead_token",
    "access_token",
    "refresh_token",
    "app_token",
    "apptoken",
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "passwd",
    "pwd",
    "cookie",
    "authorization",
    "buvid3",
    "buvid4",
    "bili_ticket",
    "sessdata",
    "bili_jct",
)

#: ``key=value`` / ``key: value`` / ``"key": "value"`` 形式的敏感对（文本脱敏用）
_SECRET_PAIR_RE = re.compile(
    rf"(?i)\b({'|'.join(re.escape(k) for k in SECRET_FIELD_KEYWORDS)})"
    r"(\s*[\"']?\s*[:=]\s*[\"']?)([^\s\"',;}\]&]+)"
)

#: ``Cookie: xxx`` / ``cookie=xxx`` 这类整段请求头
_COOKIE_HEADER_RE = re.compile(r"(?i)(\b(?:set-)?cookie\b\s*[:=]\s*)([^\n\r]+)")

#: URI 内嵌凭据 ``scheme://user:pass@host``
_URI_CREDENTIAL_RE = re.compile(r"(://[^:/@\s]+:)[^@/\s]+@")


def _is_secret_field(field_name: str) -> bool:
    key = (field_name or "").lower()
    return bool(key) and any(word in key for word in SECRET_FIELD_KEYWORDS)


def mask_text(text: str) -> str:
    """把一段文本里的密钥 / cookie 值替换成 ``****``（保留字段名，便于定位）。"""
    if not text:
        return text
    masked = _URI_CREDENTIAL_RE.sub(rf"\g<1>{MASK}@", text)
    masked = _COOKIE_HEADER_RE.sub(rf"\g<1>{MASK}", masked)
    masked = _SECRET_PAIR_RE.sub(rf"\g<1>\g<2>{MASK}", masked)
    return masked


def mask_secret(value: Any, _field_name: str = "") -> Any:
    """递归脱敏：dict / list / pydantic 模型 / 字符串。

    - 字典按**字段名**判断（``push_key`` 等整值打码），其余值递归处理；
    - 字符串先做文本级替换（``token=abc`` → ``token=****``）；
    - 其余类型原样返回。
    """
    if isinstance(value, Mapping):
        return {
            key: (MASK if _is_secret_field(str(key)) else mask_secret(val, str(key)))
            for key, val in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [mask_secret(item, _field_name) for item in value]
    if hasattr(value, "model_dump"):
        return mask_secret(value.model_dump(), _field_name)
    if isinstance(value, bytes):
        return mask_secret(value.decode("utf-8", errors="replace"), _field_name)
    if isinstance(value, str):
        if _is_secret_field(_field_name) and value:
            return MASK
        return mask_text(value)
    return value


def full_response_log_enabled() -> bool:
    """``LOG_FULL_RESPONSE=true`` 时才允许把完整响应体写进日志（默认关闭）。"""
    return os.getenv("LOG_FULL_RESPONSE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _payload_size(payload: Any) -> int:
    try:
        return len(json.dumps(payload, ensure_ascii=False, default=str))
    except (TypeError, ValueError):
        return len(str(payload))


def response_brief(
    payload: Any,
    *,
    id_keys: tuple[str, ...] = (
        "dynamic_id",
        "dynamicId",
        "dynIdStr",
        "businessId",
        "cardType",
        "uid",
        "offset",
    ),
    extra: str = "",
) -> str:
    """把一份响应 / 响应字典压成一行「可排查但不泄密」的摘要。

    只保留 ``code`` / ``message``（以及业务关键 id 与体积），绝不包含正文与 cookie。
    典型输出::

        code=-412 message=请求被拦截 size=1832 dynamic_id=11223344 extra=xxx
    """
    parts: list[str] = []
    if isinstance(payload, Mapping):
        if "code" in payload:
            parts.append(f"code={payload.get('code')}")
        message = payload.get("message") or payload.get("msg")
        if message:
            parts.append(f"message={mask_text(str(message))[:200]}")
        for key in id_keys:
            if key in payload and payload.get(key) is not None:
                parts.append(f"{key}={payload.get(key)}")
        data = payload.get("data")
        if isinstance(data, Mapping):
            for key in id_keys:
                if key in data and data.get(key) is not None:
                    parts.append(f"data.{key}={data.get(key)}")
    parts.append(f"size={_payload_size(payload)}")
    if extra:
        parts.append(f"extra={mask_text(extra)}")
    return " ".join(parts)


def format_full_response(payload: Any) -> str:
    """完整响应（已脱敏）；仅供 ``LOG_FULL_RESPONSE=true`` 时的 debug 输出。"""
    try:
        text = json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(payload)
    return mask_text(text)


__all__ = [
    "MASK",
    "SECRET_FIELD_KEYWORDS",
    "format_full_response",
    "full_response_log_enabled",
    "mask_secret",
    "mask_text",
    "response_brief",
]
