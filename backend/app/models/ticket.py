from sqlalchemy import Column, BigInteger, String, Text, Enum, DateTime, SmallInteger, ForeignKey, func
from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_no = Column(String(32), unique=True, nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text)
    source = Column(Enum("ai_auto", "manual", "feishu", name="ticket_source"), nullable=False, default="ai_auto")
    status = Column(Enum("pending", "processing", "resolved", "closed", name="ticket_status"), nullable=False, default="pending")
    priority = Column(Enum("low", "medium", "high", "urgent", name="ticket_priority"), nullable=False, default="medium")
    reporter_id = Column(BigInteger)
    reporter_name = Column(String(64))
    assignee_id = Column(BigInteger)
    solution = Column(Text)
    is_written_back = Column(SmallInteger, default=0)
    callback_note = Column(Text)
    callback_at = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id = Column(BigInteger, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(64), nullable=False)
    operator_id = Column(BigInteger)
    operator_name = Column(String(64))
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())