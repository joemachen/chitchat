"""
Alembic environment for Flask-Migrate. Uses the Flask app (from create_app) and db.metadata.
Run with: flask db upgrade / flask db migrate / flask db revision
"""
import logging
import os

from alembic import context
from flask import current_app

# Alembic Config object
config = context.config

# Configure Python logging (skip fileConfig if no alembic.ini or not found)
if config.config_file_name and os.path.isfile(config.config_file_name):
    try:
        from logging.config import fileConfig
        fileConfig(config.config_file_name)
    except Exception:
        pass
logger = logging.getLogger("alembic.env")


def get_engine():
    """Get the SQLAlchemy engine from Flask-Migrate's db extension."""
    try:
        return current_app.extensions["migrate"].db.get_engine()
    except (TypeError, AttributeError):
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    """Get the database URL for offline migrations."""
    try:
        return get_engine().url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(get_engine().url).replace("%", "%%")


def get_metadata():
    """Get SQLAlchemy metadata for autogenerate (Flask-SQLAlchemy 3.x compatible)."""
    target_db = current_app.extensions["migrate"].db
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode (generate SQL only, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url") or get_engine_url()
    context.configure(url=url, target_metadata=get_metadata(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode (connect to DB and apply)."""
    connectable = get_engine()
    conf_args = current_app.extensions["migrate"].configure_args or {}

    def process_revision_directives(ctx, revision, directives):
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
