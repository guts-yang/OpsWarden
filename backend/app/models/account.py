from sqlalchemy import Column, BigInteger, String, Enum, DateTime, func
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(String(32), unique=True, nullable=False)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    name = Column(String(64), nullable=False)
    department = Column(String(128))
    email = Column(String(128))
    phone = Column(String(20))
    role = Column(Enum("admin", "operator", "user", name="account_role"), nullable=False, default="user")
    status = Column(Enum("active", "frozen", name="account_status"), nullable=False, default="active")
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())