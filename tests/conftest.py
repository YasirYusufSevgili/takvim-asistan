import pytest

from app.infrastructure.db.session import init_db, make_engine
from app.infrastructure.repositories import SqlCommitmentRepository


@pytest.fixture
def repo():
    """Her test için temiz, bellek içi bir veritabanı."""
    engine = make_engine("sqlite://")
    init_db(engine)
    return SqlCommitmentRepository(engine)
