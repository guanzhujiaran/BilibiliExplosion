from uuid import uuid4

from Models.base.custom_pydantic import CustomBaseModelHashable


class NoneParams(CustomBaseModelHashable):
    def __hash__(self):
        return uuid4()

if __name__     == "__main__":
    print(NoneParams())