"""将 SQLAlchemy 风格的 DATABASE_URL 转为 psycopg 可用的连接串。"""


def sqlalchemy_url_to_psycopg_conninfo(url: str) -> str:
    """``postgresql+psycopg://...`` / ``postgresql+psycopg2://...`` → ``postgresql://...``"""
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url.removeprefix("postgresql+psycopg://")
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + url.removeprefix("postgresql+psycopg2://")
    return url
