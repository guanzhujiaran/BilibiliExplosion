from dataclasses import dataclass


@dataclass
class VoucherInfo:
    voucher: str
    ua: str
    generate_ts: int  # 生成时间
    ck: str
    origin: str
    referer: str
    ticket: str
    version: str
    session_id:str
