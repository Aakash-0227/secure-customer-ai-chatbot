from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

from app.database import Base
from app import models
from app import models_knowledge


# Load environment variables from the project's .env file
load_dotenv()

# Alembic configuration
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the application's SQLAlchemy models
target_metadata = Base.metadata

# Read the database URL from .env
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. Check your project's .env file."
    )

# Set the database URL for Alembic
config.set_main_option(
    "sqlalchemy.url",
    database_url.replace("%", "%%"),
)


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
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