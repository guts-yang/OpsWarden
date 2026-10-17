from sqlalchemy import Column, BigInteger, String, Text, Float, Integer, Enum, DateTime, ForeignKey, func
from pgvector.sqlalchemy import Vector

from app.database import Base

EMBEDDING_DIM = 512


class KBAnchor(Base):
    """L1 检索层：量化锚点。

    条目的联合向量经网格量化 round(v / ε) * ε 后按 quant_key 去重 upsert 到此表，
    仅本表建 IVFFlat（cosine）索引，检索时先取 Top-K 锚点再下钻 L2。
    """

    __tablename__ = "kb_anchors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quant_key = Column(String(64), unique=True, nullable=False)
    anchor_vec = Column(Vector(EMBEDDING_DIM), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class KBEntry(Base):
    """L2 检索层：页级条目。

    embedding 仅用于候选集内精排，不建向量索引；anchor_id 指向量化锚点。
    match_score 为「问题-解决方案」自检质量分（余弦相似度），由 ingest_kb_entry 覆盖写入。
    """

    __tablename__ = "kb_entries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category = Column(String(64), nullable=False)
    question = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    tags = Column(String(256))
    source = Column(
        Enum("manual", "ticket_writeback", name="kb_source", native_enum=False),
        nullable=False,
        default="manual",
    )
    match_score = Column(Float, nullable=False, default=0.8)
    anchor_id = Column(BigInteger, ForeignKey("kb_anchors.id", ondelete="RESTRICT"))
    doc_id = Column(String(128), nullable=False, default="legacy")
    page_index = Column(Integer, nullable=False, default=1)
    embedding = Column(Vector(EMBEDDING_DIM))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())