from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback


ERROR_CODES = {
    400: "请求参数错误",
    401: "未认证或Token已过期",
    403: "权限不足",
    404: "资源不存在",
    409: "数据冲突",
    422: "请求数据格式错误",
    500: "服务器内部错误",
}


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail or ERROR_CODES.get(exc.status_code, "未知错误"),
            "data": None
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "请求数据格式错误",
            "data": {"errors": errors}
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误，请稍后重试",
            "data": None
        }
    )