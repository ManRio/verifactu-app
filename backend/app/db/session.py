from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_db,
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Register all SQLAlchemy models before mapper configuration.
import app.db.models  # noqa: E402, F401


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()