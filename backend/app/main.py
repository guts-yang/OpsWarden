from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
import sys
import os

# 确保能找到 app 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine
from api import auth, account, ticket, analytics

# 直接导入异常处理函数
from middleware.exception import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
# 直接导入日志中间件类
from middleware.logging import RequestLoggingMiddleware

app = FastAPI(
    title="OpsWarden API",
    description="AI运维数字员工平台",
    version="1.0.0"
)

# 中间件（顺序很重要）
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 路由
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(ticket.router)
app.include_router(analytics.router)


@app.get("/", tags=["系统"])
def root():
    return {"message": "OpsWarden API is running", "docs": "/docs"}


@app.get("/health", tags=["系统"])
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "healthy", "database": db_status}