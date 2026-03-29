from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KBEntryCreate(BaseModel):
    category:    str          = Field(..., min_length=1, max_length=64)
    question:    str          = Field(..., min_length=1)
    solution:    str          = Field(..., min_length=1)
    tags:        Optional[str] = Field(None, max_length=256)
    match_score: Optional[float] = Field(0.8, ge=0.0, le=1.0)


class KBEntryUpdate(BaseModel):
    category:    Optional[str]   = Field(None, max_length=64)
    question:    Optional[str]   = None
    solution:    Optional[str]   = None
    tags:        Optional[str]   = Field(None, max_length=256)
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class KBEntryResponse(BaseModel):
    id:          int
    category:    str
    question:    str
    solution:    str
    tags:        Optional[str] = None
    source:      str
    match_score: float
    created_at:  datetime
    updated_at:  datetime

    class Config:
        from_attributes = True


class KBEntryListResponse(BaseModel):
    total:     int
    page:      int
    page_size: int
    items:     list[KBEntryResponse]


class KBStatsResponse(BaseModel):
    total:           int
    new_this_week:   int
    ticket_writeback: int
    avg_match_score: float
