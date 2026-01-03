"""Backend API for the Digital Twin Platform (DTP)."""

import logging
import re
from contextlib import asynccontextmanager
from time import time
from typing import Annotated, Literal
from uuid import NIL, UUID, uuid7

from dotenv import find_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose.exceptions import ExpiredSignatureError, JOSEError
from jwt_pydantic import JWTPydantic
from psycopg.errors import UniqueViolation
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from dtp.auth.db import check_password, get_session, hash_password, setup_db
from dtp.auth.models import users

BAD_USER_HEADERS = {
    "WWW-Authenticate": "Bearer",
    "X-Auth-User-ID": NIL.hex,
    "X-Auth-Roles": "",
}


# region Settings
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


class DTPSettings(BaseSettings):
    """Settings for the DTP Authentication service."""

    host: str = Field(min_length=1)
    root_path: str = Field(default="/auth")

    class Config:
        """Configuration for Pydantic Settings."""

        env_file = find_dotenv(".env")
        env_file_encoding = "utf-8"
        env_prefix = "DTP_AUTH_"
        extra = "ignore"  # Ignore extra environment variables


dtp_settings = DTPSettings()
dtp_host = dtp_settings.host
root_path = dtp_settings.root_path


class MyJWTData(BaseModel):
    """Custom JWT data model for the Digital Twin Platform.

    Pydantic model since `jwt_pydantic.JWTPydantic` does not support defaults.
    """

    iss: str = Field(default="Digital Twin Platform")  # Issuer
    sub: str  # Subject (user ID)
    iat: int = Field(default_factory=lambda: int(time()))  # Issued at (timestamp)
    jti: str = Field(default_factory=lambda: uuid7().hex)  # JWT ID


class MyJWT(JWTPydantic):
    """Custom JWT model for the Digital Twin Platform."""

    iss: str
    sub: str
    iat: int
    jti: str


# endregion Settings


# region logging
SILENT_ENDPOINTS = {"/health"}


class LogFilter(logging.Filter):
    """Filter out log messages from silent endpoints.

    See: https://dev.to/mukulsharma/taming-fastapi-access-logs-3idi
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Returns False if the record should not be logged, True otherwise."""
        if hasattr(record, "args") and len(record.args) > 2:
            path = record.args[2]
            return path not in SILENT_ENDPOINTS
        return True


logger = logging.getLogger("uvicorn.access")
logger.addFilter(LogFilter())
# endregion logging


# region fastapi
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for the FastAPI application.

    This function is called on application startup and shutdown.
    It initializes the database schema on startup.
    """
    setup_db()
    yield
    # Add any shutdown logic here if needed


app = FastAPI(
    root_path=DTPSettings().root_path,
    title="Digital Twin Platform: Authentication API",
    lifespan=lifespan,
    # docs_url=None,  # Disable Swagger UI
    # redoc_url=None,  # Disable ReDoc UI
    swagger_ui_parameters={
        # "supportedSubmitMethods": [],  # Disable "Try it out" button
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.middleware("http")
async def disable_caching(request: Request, call_next):
    """Middleware to disable caching for all responses."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# Configure CORS middleware
#
# `dtp_host` is the external hostname of the DTP backend, e.g.,
# https://dtp-docker.tailxxxxxx.ts.net or https://dtp.example.com.
# Note that `tailscale serve` is required to expose the service to the Tailnet if using Tailscale.
#
# To allow for multiple services, we expect that the frontend will be served via Traefik
# at the root path (/), and the backend API at /api/ (but also available on port 8000
# during development and testing).
#
# Note that `dtp_host` may be HTTPS, with upstream TLS termination.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Development server for Vite frontend
        "http://dtp-docker:5173",  # Development server for Vite frontend (LAN or mDNS)
        "http://localhost:8000",  # Development server for backend API
        "http://dtp-docker:8000",  # Development server for backend API (LAN or mDNS)
        "http://localhost",  # Traefik proxy for Docker deployment
        "http://dtp-docker",  # Traefik proxy for Docker deployment (LAN or mDNS)
        dtp_host,  # Traefik proxy for Docker deployment (external)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# endregion fastapi


# region endpoints
class GetTokenResponse(BaseModel):
    """Response model for token endpoint."""

    access_token: str
    token_type: Literal["bearer"]


@app.get("/health", summary="Health check endpoint", response_class=PlainTextResponse)
def health_check() -> str:
    """Health check endpoint to verify that the service is running.

    Returns:
        A simple "OK" string.
    """
    return "OK"


@app.post("/token", tags=["token"])
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
) -> GetTokenResponse:
    """Endpoint for user login and token generation."""
    query = select(users.User).where(users.User.user_name == form_data.username)
    user = session.exec(query).one_or_none()

    if not user:
        logger.warning(
            "Failed login attempt for non-existent user '%s'.",
            form_data.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers=BAD_USER_HEADERS,
        )

    if not check_password(form_data.password, user.password_hash):
        logger.warning(
            "Failed login attempt for user '%s' with incorrect password.",
            form_data.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers=BAD_USER_HEADERS,
        )

    # Generate a JWT for the authenticated user
    jwt_data = MyJWTData(sub=user.user_id.hex)
    jwt = MyJWT.new_token(
        claims=jwt_data.model_dump(mode="json"),
        key=jwt_settings.secret_key,
        algorithm=jwt_settings.algorithm,
    )

    logger.info(
        "User '%s' (%s) logged in successfully.",
        user.user_name,
        user.user_id,
    )
    return GetTokenResponse(access_token=jwt, token_type="bearer")


class CheckRole:
    """Dependency class to check if the user has a required role.

    Args:
        roles (str | None): Comma-separated string of roles to check for.
            User must have at least one of these roles. If roles is None, we only check
            if the user is authenticated.  Converted to `set[str] | None` internally.
    """

    def __init__(self, roles: str | None):
        self.roles = set(roles.split(",")) if roles else None
        """List of roles to check for.  User must have at least one of these roles.

        If None, only checks if the user is authenticated.
        """

    def __call__(
        self,
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Annotated[Session, Depends(get_session)],
        response: Response,
    ):
        """Dependency to check if the user has a required role."""
        try:
            jwt = MyJWT(
                token,
                key=jwt_settings.secret_key,
                algorithm=jwt_settings.algorithm,
            )
        except ExpiredSignatureError:
            # We do not currently set token expiration, but handle it just in case
            logger.warning("Expired token used for authentication.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers=BAD_USER_HEADERS,
            )
        except JOSEError:  # Catch all other JWT-related errors
            logger.warning("Invalid token used for authentication.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers=BAD_USER_HEADERS,
            )

        user_id = UUID(jwt.sub)
        query = select(users.User).where(users.User.user_id == user_id)

        user = session.exec(query).one_or_none()

        if not user:
            logger.warning("Token used for non-existent user ID '%s'.", user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers=BAD_USER_HEADERS,
            )

        if "admin" in [role.role_name for role in user.roles]:
            # Admins have access to everything
            pass
        elif self.roles is None:
            # No specific role required, just authenticated
            pass
        elif not self.roles.intersection(role.role_name for role in user.roles):
            # User does not have any of the allowed roles
            logger.warning(
                "User '%s' (%s) does not have required roles: %s.",
                user.user_name,
                user.user_id,
                ",".join(self.roles),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
                headers=BAD_USER_HEADERS,
            )

        response.headers["X-Auth-User-ID"] = user.user_id.hex
        response.headers["X-Auth-Roles"] = ",".join(role.role_name for role in user.roles)

        return user


class UserInfo(BaseModel):
    """Response model for user info endpoint."""

    user_id: str
    user_name: str
    roles: list[str]


@app.get(
    "/users/me",
    summary="Get current user info",
    tags=["users"],
)
def get_current_user_info(
    user: Annotated[users.User, Depends(CheckRole(None))],
) -> UserInfo:
    """Endpoint to get current user info."""
    # CheckRole(None) ensures the user is authenticated, so just return the user info from there
    logger.info(
        "User '%s' (%s) retrieved their user info.",
        user.user_name,
        user.user_id,
    )
    return UserInfo(
        user_id=str(user.user_id),
        user_name=user.user_name,
        roles=[role.role_name for role in user.roles],
    )


class UsersList(BaseModel):
    """Response model for users list endpoint."""

    users: list[UserInfo]


@app.get(
    "/users",
    summary="Get list of all users",
    tags=["users"],
)
def get_users_list(
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> UsersList:
    """Endpoint to get list of all users.  Admin only."""
    query = select(users.User)
    all_users = session.exec(query).all()

    logger.info(
        "Admin '%s' (%s) retrieved list of all users (%d users).",
        admin_user.user_name,
        admin_user.user_id,
        len(all_users),
    )
    return UsersList(
        users=[
            UserInfo(
                user_id=str(user.user_id),
                user_name=user.user_name,
                roles=[role.role_name for role in user.roles],
            )
            for user in all_users
        ]
    )


class UpdateUserInfoRequest(BaseModel):
    """Request model for updating user info."""

    new_username: str | None = Field(default=None, description="New username")
    current_password: str = Field(description="Current password")
    new_password: str | None = Field(default=None, description="New password")


@app.patch(
    "/users/me",
    summary="Change current user info",
    tags=["users"],
)
def update_current_user_info(
    user: Annotated[users.User, Depends(CheckRole(None))],
    session: Annotated[Session, Depends(get_session)],
    new_user_info: UpdateUserInfoRequest,
) -> UserInfo:
    """Endpoint to update current user info."""
    # CheckRole(None) ensures the user is authenticated
    if not new_user_info.new_username and not new_user_info.new_password:
        logger.warning(
            "Attempt to update user info for '%s' (%s), but no changes specified.",
            user.user_name,
            user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes specified",
        )

    if not new_user_info.current_password:
        logger.warning(
            "Attempt to update user info for '%s' (%s), but current password not provided.",
            user.user_name,
            user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is required to change user info",
        )
    if not check_password(new_user_info.current_password, user.password_hash):
        logger.warning(
            "Attempt to update user info for '%s' (%s), but incorrect current password provided.",
            user.user_name,
            user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    pattern = r"[\u0020-\u007F]+$"  # printable ASCII characters only
    if new_user_info.new_username:
        if user.user_name == "admin":
            logger.warning("Attempt to change username of the 'admin' user.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change username of admin user",
            )
        if new_user_info.new_username == "admin":
            logger.warning(
                "Attempt to change username to reserved 'admin' (current: %s).", user.user_name
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username 'admin' is reserved",
            )
        if new_user_info.new_username.strip() == "":
            logger.warning(
                "Attempt to change username to empty string (current: %s).", user.user_name
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username cannot be empty",
            )
        if not re.match(pattern, new_user_info.new_username):
            logger.warning(
                "Attempt to change username to non-printable ASCII characters (current: %s).",
                user.user_name,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must contain only printable ASCII characters",
            )
        user.user_name = new_user_info.new_username

    if new_user_info.new_password:
        if new_user_info.new_password.strip() == "":
            logger.warning(
                "Attempt to change password to empty string (current user: %s).", user.user_name
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be empty",
            )
        if not re.match(pattern, new_user_info.new_password):
            logger.warning(
                "Attempt to change password to non-printable ASCII characters (current user: %s).",
                user.user_name,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must contain only printable ASCII characters",
            )
        user.password_hash = hash_password(new_user_info.new_password)

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except IntegrityError as e:
        session.rollback()
        orig = e.orig  # Extract the original exception from the SQLAlchemy exception
        if isinstance(orig, UniqueViolation) and orig.diag.constraint_name == "ix_user_user_name":
            # Username already exists
            logger.warning(
                "Attempt to change username to already taken username '%s' (current: %s).",
                new_user_info.new_username,
                user.user_name,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken",
            ) from e
        # Not a username unique violation, re-raise as generic error
        logger.error(
            "Failed to update user info for user '%s' (%s): %s",
            user.user_name,
            user.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user info",
        ) from e
    # Catch all other database errors
    except Exception as e:
        session.rollback()
        logger.error(
            "Failed to update user info for user '%s' (%s): %s",
            user.user_name,
            user.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user info",
        ) from e

    logger.info(
        "User '%s' (%s) successfully updated their user info.", user.user_name, user.user_id
    )
    return UserInfo(
        user_id=str(user.user_id),
        user_name=user.user_name,
        roles=[role.role_name for role in user.roles],
    )


@app.get(
    "/users/search",
    summary="Search for user by username",
    tags=["users"],
)
def search_user_by_username(
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
    username_query: Annotated[str, Query(description="Username to search for")],
) -> UserInfo:
    """Endpoint to search for users by username.  Admin only."""
    if not username_query:
        logger.warning(
            "Admin '%s' (%s) searched with an empty username query.",
            admin_user.user_name,
            admin_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username query cannot be empty",
        )
    logger.info(
        "Admin '%s' (%s) is searching for user with username '%s'.",
        admin_user.user_name,
        admin_user.user_id,
        username_query,
    )
    query = select(users.User).where(users.User.user_name == username_query)
    user = session.exec(query).one_or_none()
    if not user:
        logger.info(
            "No user found with username '%s' by admin '%s' (%s).",
            username_query,
            admin_user.user_name,
            admin_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    logger.info(
        "Admin '%s' (%s) found user '%s' (%s) with username '%s'.",
        admin_user.user_name,
        admin_user.user_id,
        user.user_name,
        user.user_id,
        username_query,
    )
    return UserInfo(
        user_id=str(user.user_id),
        user_name=user.user_name,
        roles=[role.role_name for role in user.roles],
    )


@app.post(
    "/users",
    summary="Create a new user",
    tags=["users"],
)
def create_new_user(
    user_name: Annotated[str, Query(description="Username for the new user")],
    password: Annotated[str, Query(description="Password for the new user")],
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> UserInfo:
    """Endpoint to create a new user.  Admin only."""
    if not user_name.strip():
        logger.warning(
            "Admin '%s' (%s) attempted to create a user with an empty username.",
            admin_user.user_name,
            admin_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty",
        )
    if not password.strip():
        logger.warning(
            "Admin '%s' (%s) attempted to create a user with an empty password.",
            admin_user.user_name,
            admin_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty",
        )

    new_user = users.User(
        user_name=user_name,
        password_hash=hash_password(password),
    )
    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    except IntegrityError as e:
        session.rollback()
        orig = e.orig  # Extract the original exception from the SQLAlchemy exception
        if isinstance(orig, UniqueViolation) and orig.diag.constraint_name == "ix_user_user_name":
            # Username already exists
            logger.warning(
                "Admin '%s' (%s) attempted to create already existing user '%s'.",
                admin_user.user_name,
                admin_user.user_id,
                user_name,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            ) from e
        # Not a username unique violation, re-raise as generic error
        logger.error(
            "Failed to create new user '%s' by admin '%s' (%s): %s",
            user_name,
            admin_user.user_name,
            admin_user.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create new user",
        ) from e
    except Exception as e:
        session.rollback()
        logger.error(
            "Failed to create new user '%s' by admin '%s' (%s): %s",
            user_name,
            admin_user.user_name,
            admin_user.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create new user",
        ) from e
    logger.info(
        "Admin '%s' (%s) created new user '%s' (%s).",
        admin_user.user_name,
        admin_user.user_id,
        new_user.user_name,
        new_user.user_id,
    )
    return UserInfo(
        user_id=str(new_user.user_id),
        user_name=new_user.user_name,
        roles=[role.role_name for role in new_user.roles],  # Should be empty list
    )


@app.delete(
    "/users/{user_id}",
    summary="Delete a user",
    tags=["users"],
)
def delete_user(
    user_id: Annotated[UUID, Path(description="ID of the user to delete")],
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> UserInfo:
    """Endpoint to delete a user.  Admin only."""
    query = select(users.User).where(users.User.user_id == user_id)
    user = session.exec(query).one_or_none()
    if not user:
        logger.warning(
            "Admin '%s' (%s) attempted to delete non-existent user (%s).",
            admin_user.user_name,
            admin_user.user_id,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.user_name == "admin":
        logger.warning(
            "Attempt by '%s' (%s) to delete the reserved 'admin' user.",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin user",
        )

    session.delete(user)
    session.commit()
    logger.info(
        "Admin '%s' (%s) deleted user '%s' (%s).",
        admin_user.user_name,
        admin_user.user_id,
        user.user_name,
        user.user_id,
    )
    return UserInfo(
        user_id=str(user.user_id),
        user_name=user.user_name,
        roles=[role.role_name for role in user.roles],
    )


class RoleInfo(BaseModel):
    """Response model for role info endpoint."""

    role_id: str
    role_name: str


class RolesList(BaseModel):
    """Response model for roles list endpoint."""

    roles: list[RoleInfo]


@app.get(
    "/roles",
    summary="Get list of all roles",
    tags=["roles"],
)
def get_roles_list(
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> RolesList:
    """Endpoint to get list of all roles.  Admin only."""
    query = select(users.Role)
    all_roles = session.exec(query).all()

    logger.info(
        "Admin '%s' (%s) retrieved list of all roles (%d roles).",
        admin_user.user_name,
        admin_user.user_id,
        len(all_roles),
    )
    return RolesList(
        roles=[RoleInfo(role_id=str(role.role_id), role_name=role.role_name) for role in all_roles]
    )


class UserInfoWithoutRoles(BaseModel):
    """Response model for user info without roles."""

    user_id: str
    user_name: str


class UsersInRole(BaseModel):
    """Response model for users in role endpoint."""

    users: list[UserInfoWithoutRoles]


@app.get(
    "/roles/{role_name}/users",
    summary="Get list of users with a specific role",
    tags=["roles"],
)
def get_users_in_role(
    role_name: Annotated[str, Path(description="Name of the role to get users for")],
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> UsersInRole:
    """Endpoint to get list of users with a specific role.  Admin only."""
    if not role_name:
        logger.warning(
            "Admin '%s' (%s) requested users for an empty role name.",
            admin_user.user_name,
            admin_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name cannot be empty",
        )

    query_role = select(users.Role).where(users.Role.role_name == role_name)
    role = session.exec(query_role).one_or_none()
    if not role:
        logger.warning(
            "Admin '%s' (%s) attempted to get users for non-existent role '%s'.",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    logger.info(
        "Admin '%s' (%s) retrieved list of users with role '%s' (%d users).",
        admin_user.user_name,
        admin_user.user_id,
        role.role_name,
        len(role.users),
    )
    return UsersInRole(
        users=[
            UserInfoWithoutRoles(
                user_id=str(user.user_id),
                user_name=user.user_name,
            )
            for user in role.users
        ]
    )


@app.post(
    "/roles/{role_name}",
    summary="Create a new role",
    tags=["roles"],
)
def create_new_role(
    role_name: Annotated[str, Path(description="Name of the new role to create")],
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> RoleInfo:
    """Endpoint to create a new role.  Admin only."""
    if not role_name.strip():
        logger.warning(
            "Admin '%s' (%s) attempted to create a role with an empty name.",
            admin_user.user_name,
            admin_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name cannot be empty",
        )

    new_role = users.Role(role_name=role_name)
    try:
        session.add(new_role)
        session.commit()
        session.refresh(new_role)
    except IntegrityError as e:
        session.rollback()
        if (
            isinstance(e.orig, UniqueViolation)
            and e.orig.diag.constraint_name == "ix_role_role_name"
        ):
            # Role name already exists
            logger.warning(
                "Admin '%s' (%s) attempted to create already existing role '%s'.",
                admin_user.user_name,
                admin_user.user_id,
                role_name,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role already exists",
            ) from e
        # Not a role name unique violation, re-raise as generic error
        logger.error(
            "Failed to create new role '%s' by admin '%s' (%s): %s",
            role_name,
            admin_user.user_name,
            admin_user.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create new role",
        ) from e
    except Exception as e:
        session.rollback()
        logger.error(
            "Failed to create new role '%s' by admin '%s' (%s): %s",
            role_name,
            admin_user.user_name,
            admin_user.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create new role",
        ) from e
    logger.info(
        "Admin '%s' (%s) created new role '%s' (%s).",
        admin_user.user_name,
        admin_user.user_id,
        new_role.role_name,
        new_role.role_id,
    )
    return RoleInfo(role_id=str(new_role.role_id), role_name=new_role.role_name)


@app.delete(
    "/roles/{role_name}",
    summary="Delete a role",
    tags=["roles"],
)
def delete_role(
    role_name: Annotated[str, Path(description="Name of the role to delete")],
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> RoleInfo:
    """Endpoint to delete a role.  Admin only."""
    if role_name == "admin":
        logger.warning(
            "Attempt by '%s' (%s) to delete the reserved 'admin' role.",
            admin_user.user_name,
            admin_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin role",
        )

    query_role = select(users.Role).where(users.Role.role_name == role_name)
    role = session.exec(query_role).one_or_none()
    if not role:
        logger.warning(
            "Admin '%s' (%s) attempted to delete non-existent role '%s'.",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Prevent role deletion if any users have this role assigned
    if role.users:
        logger.warning(
            "Admin '%s' (%s) attempted to delete role '%s' which is assigned to %d user(s).",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
            len(role.users),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role assigned to users",
        )

    try:
        session.delete(role)
        session.commit()
    except Exception as e:
        # Catch all database errors
        session.rollback()
        logger.error(
            "Failed to delete role '%s' by admin '%s' (%s): %s",
            role_name,
            admin_user.user_name,
            admin_user.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete role",
        ) from e

    logger.info(
        "Admin '%s' (%s) deleted role '%s' (%s).",
        admin_user.user_name,
        admin_user.user_id,
        role.role_name,
        role.role_id,
    )
    return RoleInfo(role_id=str(role.role_id), role_name=role.role_name)


@app.post(
    "/users/{user_id}/roles/{role_name}",
    summary="Assign a role to a user",
    tags=["userroles"],
)
def assign_role_to_user(
    user_id: UUID,
    role_name: str,
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> UserInfo:
    """Endpoint to assign a role to a user.  Admin only."""
    query_user = select(users.User).where(users.User.user_id == user_id)
    user = session.exec(query_user).one_or_none()
    if not user:
        logger.warning(
            "Admin '%s' (%s) attempted to assign role '%s' to non-existent user ID '%s'.",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    query_role = select(users.Role).where(users.Role.role_name == role_name)
    role = session.exec(query_role).one_or_none()
    if not role:
        logger.warning(
            "Admin '%s' (%s) attempted to assign non-existent role '%s' to user ID '%s'.",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if role in user.roles:
        logger.info(
            "Admin '%s' (%s) attempted to assign role '%s' to user ID '%s', but the user "
            "already has this role.",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
            user_id,
        )
    else:
        try:
            user.roles.append(role)
            session.add(user)
            session.commit()
            session.refresh(user)
        except Exception as e:
            # Catch all database errors
            session.rollback()
            logger.error(
                "Failed to assign role '%s' to user '%s' (%s) by admin '%s' (%s): %s",
                role_name,
                user.user_name,
                user.user_id,
                admin_user.user_name,
                admin_user.user_id,
                str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign role to user",
            ) from e

        logger.info(
            "Admin '%s' (%s) assigned role '%s' to user '%s' (%s).",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
            user.user_name,
            user.user_id,
        )

    return UserInfo(
        user_id=str(user.user_id),
        user_name=user.user_name,
        roles=[r.role_name for r in user.roles],
    )


@app.delete(
    "/users/{user_id}/roles/{role_name}",
    summary="Remove a role from a user",
    tags=["userroles"],
)
def remove_role_from_user(
    user_id: UUID,
    role_name: str,
    session: Annotated[Session, Depends(get_session)],
    admin_user: Annotated[users.User, Depends(CheckRole("admin"))],
) -> UserInfo:
    """Endpoint to remove a role from a user.  Admin only."""
    # Check for empty role name
    if not role_name:
        logger.warning(
            "Admin '%s' (%s) attempted to remove an empty role name from user ID '%s'.",
            admin_user.user_name,
            admin_user.user_id,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name cannot be empty",
        )

    query_user = select(users.User).where(users.User.user_id == user_id)
    user = session.exec(query_user).one_or_none()

    # Check if user exists
    if not user:
        logger.warning(
            "Admin '%s' (%s) attempted to remove role '%s' from non-existent user ID '%s'.",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent removing 'admin' role from 'admin' user
    if user.user_name == "admin" and role_name == "admin":
        logger.warning(
            "Attempt by '%s' (%s) to remove the 'admin' role from the 'admin' user.",
            admin_user.user_name,
            admin_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin role from admin user",
        )

    query_role = select(users.Role).where(users.Role.role_name == role_name)
    role = session.exec(query_role).one_or_none()

    # Check if role exists
    if not role:
        logger.warning(
            "Admin '%s' (%s) attempted to remove non-existent role '%s' from user ID '%s'.",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
            user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Check if user has the role
    if role not in user.roles:
        logger.warning(
            "Admin '%s' (%s) attempted to remove role '%s' from user '%s' (%s), but user does "
            "not have the role.",
            admin_user.user_name,
            admin_user.user_id,
            role_name,
            user.user_name,
            user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have the specified role",
        )
    # Remove the role from the user
    try:
        user.roles.remove(role)
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception as e:
        # Catch all database errors
        session.rollback()
        logger.error(
            "Failed to remove role '%s' from user '%s' (%s) by admin '%s' (%s): %s",
            role_name,
            user.user_name,
            user.user_id,
            admin_user.user_name,
            admin_user.user_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove role from user",
        ) from e

    logger.info(
        "Admin '%s' (%s) removed role '%s' from user '%s' (%s).",
        admin_user.user_name,
        admin_user.user_id,
        role_name,
        user.user_name,
        user.user_id,
    )

    return UserInfo(
        user_id=str(user.user_id),
        user_name=user.user_name,
        roles=[r.role_name for r in user.roles],
    )


# endregion endpoints
