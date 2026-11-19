from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine


def make_engine(url: str = "sqlite:///soz.db") -> Engine:
    """SQLite bağlantısı. 'sqlite://' (bellek içi) testlerde kullanılır."""
    if url == "sqlite://":
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, connect_args={"check_same_thread": False})


def init_db(engine: Engine) -> None:
    """Tabloları oluşturur (varsa dokunmaz)."""
    from app.infrastructure.db import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
