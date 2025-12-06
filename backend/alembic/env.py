from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from modules.connection_to_db.database import Base
from modules.models.models_alembic_import import *
from modules.utils.config import settings

config = context.config


def _normalize(url: str) -> str:
    return (
        url.replace("postgresql+asyncpg://", "postgresql+psycopg2://") if url else url
    )


def _choose_url() -> str:

    x = context.get_x_argument(as_dictionary=True)
    if x and x.get("db_url"):
        return x["db_url"]

    if settings.DATABASE_URL:
        return settings.DATABASE_URL

    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return ini_url

    raise RuntimeError("No database URL found for Alembic")


sync_url = _normalize(_choose_url())
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
