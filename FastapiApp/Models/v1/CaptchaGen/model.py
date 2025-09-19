from enum import StrEnum, Enum

from Models.base.custom_pydantic import CustomBaseModel


class CaptchaGenResp(CustomBaseModel):
    captcha_id: str
    image: str


class CaptchaVerifyReq(CustomBaseModel):
    captcha_id: str
    input_text: str


class CaptchaVerifyStatusEnum(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"


class CaptchaVerifyStatus:
    value: str
    __code = {
        "VALID": 0,
        "INVALID": 400,
        "EXPIRED": 2,
    }
    __message = {
        "VALID": "",
        "INVALID": "验证码错误，请重新输入！",
        "EXPIRED": "验证码已过期，请重新获取！",
    }

    def __init__(self, value: CaptchaVerifyStatusEnum):
        self.value = value

    def set_value(self, value) -> "CaptchaVerifyStatus":
        self.value = value
        return self

    @property
    def code(self) -> int:
        return self.__code.get(self.value, 400)

    @property
    def message(self) -> str:
        return self.__message.get(self.value, "验证码错误，请重新输入！")

    @property
    def success(self) -> bool:
        return self.value == "VALID"


if __name__ == '__main__':
    a= CaptchaVerifyStatus(value=CaptchaVerifyStatusEnum.VALID)
    print(a.success)
    print(a.code)
    print(a.message)
