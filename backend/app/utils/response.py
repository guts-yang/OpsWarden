from typing import Any


def success(data: Any = None, message: str = "success") -> dict:
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error(code: int = 400, message: str = "error", data: Any = None) -> dict:
    return {
        "code": code,
        "message": message,
        "data": data
    }