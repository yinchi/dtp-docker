"""Module for interacting with the central Digital Twin Platform database."""

import logging
from collections.abc import Generator

import bcrypt
import sqlmodel
import timescaledb
from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from sqlmodel import Session, select
from timescaledb.engine import create_engine


class Settings(BaseSettings):
    """Settings for the Digital Twin Platform database connection."""

    db_hostname: str = Field(min_length=1)
    db_port: int = Field(ge=1, le=65535)
    db_name: str = Field(min_length=1)
    db_username: str = Field(min_length=1)
    db_password: str = Field(min_length=1)
    bootstrap_admin_password: str = Field(
        min_length=1,
        title="DT platform bootstrap password",
        description="Initial password for the 'admin' user used during bootstrapping.",
    )

    class Config:
        """Configuration for Pydantic Settings."""

        env_file = find_dotenv(".env")
        env_file_encoding = "utf-8"
        env_prefix = "DTP_"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
db_url = (
    "postgresql+psycopg://"
    f"{settings.db_username}:{settings.db_password}"
    f"@{settings.db_hostname}:{settings.db_port}"
    f"/{settings.db_name}"
)
engine = create_engine(db_url, timezone="UTC", echo=False)


def get_session() -> Generator[Session, None, None]:
    """Get a new database session.

    Yields:
        SQLModel Session instance
    """
    with Session(engine) as session:
        yield session


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    """Check a plaintext password against a hashed password."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def setup_db() -> None:
    """Initialize the database schema."""
    from dtp.models import users  # noqa: F401,PLC0415

    sqlmodel.SQLModel.metadata.create_all(engine, checkfirst=True)
    timescaledb.metadata.create_all(engine)

    with Session(engine) as session:
        query_user = select(users.User).where(users.User.user_name == "admin")
        admin_user = session.exec(query_user).one_or_none()

        # Ensure the 'admin' user exists
        if admin_user is None:
            admin_user = users.User(
                user_name="admin",
                password_hash=hash_password(settings.db_bootstrap_admin_password),
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            logging.info(
                "Created user '%s' user in the database (%s).",
                admin_user.user_name,
                admin_user.user_id,
            )
        else:
            logging.info(
                "Admin user '%s' already exists in the database (%s).",
                admin_user.user_name,
                admin_user.user_id,
            )

        # Ensure the 'admin' role exists
        query_role = select(users.Role).where(users.Role.role_name == "admin")
        admin_role = session.exec(query_role).one_or_none()
        if admin_role is None:
            admin_role = users.Role(role_name="admin")
            session.add(admin_role)
            session.commit()
            session.refresh(admin_role)
            logging.info(
                "Created role '%s' role in the database (%s).",
                admin_role.role_name,
                admin_role.role_id,
            )
        else:
            logging.info(
                "Admin role '%s' already exists in the database (%s).",
                admin_role.role_name,
                admin_role.role_id,
            )

        # Ensure the 'admin' user has the 'admin' role
        # Since we set `back_populates` on both sides, we can just append to one side
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            session.refresh(admin_role)
            logging.info(
                "Assigned role '%s' to user '%s' in the database.",
                admin_role.role_name,
                admin_user.user_name,
            )
        else:
            logging.info(
                "User '%s' already has role '%s' assigned in the database.",
                admin_user.user_name,
                admin_role.role_name,
            )
