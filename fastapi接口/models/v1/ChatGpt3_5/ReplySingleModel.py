from pydantic import BaseModel

class ReplyReq(BaseModel):
    """
    请求内容
    """
    question: str
    ts:int

class ReplyRes(BaseModel):
    """
    ai回复内容
    """
    answer:str
    ts:int