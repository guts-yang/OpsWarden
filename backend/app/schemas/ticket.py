from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TicketStatusEnum(str, Enum):
    pending = "pending"
    processing = "processing"
    resolved = "resolved"
    closed = "closed"


class TicketSourceEnum(str, Enum):
    ai_auto = "ai_auto"
    manual = "manual"
    feishu = "feishu"


class TicketPriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TicketAutoCreate(BaseModel):
    title: str = Field(..., description="用户的问题")
    description: Optional[str] = Field(None)
    reporter_name: Optional[str] = Field(None)
    source: TicketSourceEnum = Field(default=TicketSourceEnum.ai_auto)


class TicketManualCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256, description="工单标题")
    description: Optional[str] = Field(None, description="问题详细描述")
    priority: TicketPriorityEnum = Field(default=TicketPriorityEnum.medium, description="优先级")


class TicketUpdate(BaseModel):
    status: Optional[TicketStatusEnum] = None
    assignee_id: Optional[int] = None
    solution: Optional[str] = None
    priority: Optional[TicketPriorityEnum] = None


class TicketResolve(BaseModel):
    solution: str = Field(..., description="解决方案")
    write_back: bool = Field(default=True, description="是否回写知识库")


class TicketCallback(BaseModel):
    callback_note: str = Field(..., description="回访备注")


class TicketResponse(BaseModel):
    id: int
    ticket_no: str
    title: str
    description: Optional[str] = None
    source: str
    status: str
    priority: str
    reporter_id: Optional[int] = None
    reporter_name: Optional[str] = None
    assignee_id: Optional[int] = None
    solution: Optional[str] = None
    is_written_back: int
    callback_note: Optional[str] = None
    callback_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TicketResponse]


class TicketLogResponse(BaseModel):
    id: int
    ticket_id: int
    action: str
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True