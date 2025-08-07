from fastapi接口.models.base.custom_pydantic import CustomBaseModel


class VoucherInfo(CustomBaseModel):
    voucher: str | None
    ua: str | None
    generate_ts: int | None  # 生成时间
    ck: str | None
    origin: str | None
    referer: str | None
    ticket: str | None
    version: str | None
    session_id: str | None
