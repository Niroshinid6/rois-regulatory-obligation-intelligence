from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app import models
from app.core.config import settings
from app.core.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.normalized_migration_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    migration_url = settings.normalized_migration_database_url
    connect_args = {"check_same_thread": False} if migration_url.startswith("sqlite") else {}
    if migration_url.lower().startswith("postgresql") and (
        ":6543/" in migration_url.lower() or "pgbouncer=true" in migration_url.lower()
    ):
        connect_args["prepare_threshold"] = 0
    engine = create_engine(
        migration_url,
        poolclass=NullPool,
        connect_args=connect_args,
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
