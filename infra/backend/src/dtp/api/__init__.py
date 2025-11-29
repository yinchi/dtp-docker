"""Backend API for the Digital Twin Platform (DTP)."""

from contextlib import asynccontextmanager
from pprint import pprint
from time import time
from typing import Annotated
from uuid import UUID, uuid7

from dotenv import find_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose.exceptions import ExpiredSignatureError, JOSEError
from jwt_pydantic import JWTPydantic
from pydantic import Field
from pydantic_settings import BaseSettings
from sqlmodel import Session, select

from dtp.api.db import check_password, get_session, setup_db
from dtp.api.db import settings as db_settings
from dtp.models import users


class JWTSettings(BaseSettings):
    """Settings for JWT configuration."""

    secret_key: bytes = Field(min_length=32)
    algorithm: str = Field(default="HS256")

    class Config:
        """Configuration for Pydantic Settings."""

        env_file = find_dotenv(".env")
        env_file_encoding = "utf-8"
        env_prefix = "DTP_JWT_"
        extra = "ignore"  # Ignore extra environment variables


jwt_settings = JWTSettings()


class MyJWT(JWTPydantic):
    """Custom JWT model for the Digital Twin Platform."""

    iss: str = Field(default="Digital Twin Platform")  # Issuer
    sub: str  # Subject (user ID)
    iat: int = Field(default_factory=time)  # Issued at (timestamp)
    jti: str = Field(default_factory=lambda: uuid7().hex)  # JWT ID


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for the FastAPI application.

    This function is called on application startup and shutdown.
    It initializes the database schema on startup.
    """
    setup_db()
    yield
    # Add any shutdown logic here if needed


app = FastAPI(title="Digital Twin Platform API", lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.post("/token")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    """Endpoint for user login and token generation."""
    query = select(users.User).where(users.User.user_name == form_data.username)
    user = session.exec(query).one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not check_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate a JWT for the authenticated user
    jwt = MyJWT.new_token(
        claims={"sub": user.user_id.hex},
        key=jwt_settings.secret_key,
        algorithm=jwt_settings.algorithm,
    )

    return {"access_token": jwt, "token_type": "bearer"}


class CheckRole:
    """Dependency class to check if the user has the required role.

    If no role is specified, it only checks if the user is authenticated.
    """

    def __init__(self, required_role: str | None):
        self.required_role = required_role

    def __call__(
        self,
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Annotated[Session, Depends(get_session)],
        response: Response,
    ):
        """Dependency to check if the user has the required role."""
        try:
            jwt = MyJWT(
                token,
                key=jwt_settings.secret_key,
                algorithm=jwt_settings.algorithm,
            )
        except ExpiredSignatureError:
            # We do not currently set token expiration, but handle it just in case
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JOSEError:  # Catch all other JWT-related errors
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = UUID(jwt.sub)
        query = select(users.User).where(users.User.user_id == user_id)

        user = session.exec(query).one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if self.required_role and self.required_role not in [role.role_name for role in user.roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        response.headers["X-Auth-User-ID"] = str(user.user_id)

        return user


@app.get(
    "/user/me",
    summary="Get current user info",
)
def get_current_user_info(
    user: Annotated[users.User, Depends(CheckRole(None))],
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, str | list[str]]:
    """Endpoint to get current user info."""
    query = select(users.User).where(users.User.user_name == "admin")
    user = session.exec(query).one()
    return {
        "user_id": str(user.user_id),
        "user_name": user.user_name,
        "roles": [role.role_name for role in user.roles],
    }


@app.get(
    "/user",
    summary="Get all users",
    dependencies=[Depends(CheckRole("admin"))],
)
def get_all_users(
    session: Annotated[Session, Depends(get_session)],
) -> list[dict[str, str | list[str]]]:
    """Endpoint to get all users (admin only).

    In a production system, this would likely be paginated and there would be another
    endpoint to get the total user count (and thus number of pages).
    """
    query = select(users.User).order_by(users.User.user_name)
    all_users = session.exec(query).all()
    return [
        {
            "user_id": str(user.user_id),
            "user_name": user.user_name,
            "roles": [role.role_name for role in user.roles],
        }
        for user in all_users
    ]


def main():
    """Main entrypoint."""
    # For now, just confirm that we can load settings.
    pprint(db_settings.model_dump(mode="json"))
    # TODO: set argv[] and call fastapi.cli.main()
