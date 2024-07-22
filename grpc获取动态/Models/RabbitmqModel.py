from dataclasses import dataclass


@dataclass
class VoucherInfo:
    voucher: str
    ua: str
    generate_ts: int  # 生成时间

