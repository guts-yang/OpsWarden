from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import engine

app = FastAPI(
    title="OpsWarden API",
    description="AI运维数字员工平台",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["系统"])
def root():
    return {"message": "OpsWarden API is running", "docs": "/docs"}


@app.get("/health", tags=["系统"])
def health_check():
    """健康检查：同时验证数据库连接"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status
    }