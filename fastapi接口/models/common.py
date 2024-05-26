from fastapi import status
from fastapi.responses import JSONResponse, Response
from typing import Union


def resp_0(*, data: Union[list, dict, str]) -> Response:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'code': 0,
            'message': "Success",
            'data': data,
        }
    )

def resp_400(*, data: str = None, message: str = "请求参数缺失") -> Response:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            'code': -400,
            'message': message,
            'data': data,
        }
    )


def resp_412(*, data: str = None, message: str = "请求过快") -> Response:
    return JSONResponse(
        status_code=status.HTTP_412_PRECONDITION_FAILED,
        content={
            'code': -412,
            'message': message,
            'data': data,
        }
    )


def resp_500(*, data: str = None, message: str = "内部错误") -> Response:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'code': 500,
            'message': message,
            'data': data,
        }
    )
