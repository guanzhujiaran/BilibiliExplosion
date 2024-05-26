import http
import json

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from fastapi接口.router.v1.ChatGpt3_5 import ReplySingle
from fastapi接口.models.common import resp_500, resp_412
from starlette.requests import Request



app = FastAPI()
app.include_router(ReplySingle.router)

@app.middleware('http')
async def common_response(request: Request,call_next):
    response = await call_next(request)
    body = [section async for section in response.body_iterator]
    original_body = b"".join(body).decode()
    status_code = response.status_code
    response.body_iterator = iter([json.dumps({
        "code": 0,
        "message": "Success" if status_code == 200 else "Error",
        "data": json.loads(original_body) if original_body else None
    }).encode()])
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, e: Exception):
    return resp_500(
        data=str(e)
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, e: RequestValidationError):
    return resp_412(
        data=str(e)
    )

