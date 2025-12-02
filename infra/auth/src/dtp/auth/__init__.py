"""Backend API for the Digital Twin Platform (DTP)."""

from contextlib import asynccontextmanager
from time import time
from typing import Annotated, Literal
from uuid import NIL, UUID, uuid7

from dotenv import find_dotenv
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose.exceptions import ExpiredSignatureError, JOSEError
from jwt_pydantic import JWTPydantic
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from sqlmodel import Session, select

from dtp.auth.db import check_password, get_session, setup_db
from dtp.models import users

BAD_USER_HEADERS = {
    "WWW-Authenticate": "Bearer",
    "X-Auth-User-ID": NIL.hex,
    "X-Auth-Roles": "",
}


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
    """Settings for JWT configuration."""

    host: str = Field(min_length=1)
    root_path: str = Field(default="/auth")

    class Config:
        """Configuration for Pydantic Settings."""

        env_file = find_dotenv(".env")
        env_file_encoding = "utf-8"
        env_prefix = "DTP_AUTH_"
        extra = "ignore"  # Ignore extra environment variables


dtp_host = DTPSettings().host


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
        f"{dtp_host}:5173",  # Development server for Vite frontend (external)
        "http://localhost:8000",  # Development server for backend API
        "http://dtp-docker:8000",  # Development server for backend API (LAN or mDNS)
        f"{dtp_host}:8000",  # Development server for backend API (external)
        "http://localhost",  # Traefik proxy for Docker deployment
        "http://dtp-docker",  # Traefik proxy for Docker deployment (LAN or mDNS)
        dtp_host,  # Traefik proxy for Docker deployment (external)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers=BAD_USER_HEADERS,
        )

    if not check_password(form_data.password, user.password_hash):
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

    return GetTokenResponse(access_token=jwt, token_type="bearer")


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
                headers=BAD_USER_HEADERS,
            )
        except JOSEError:  # Catch all other JWT-related errors
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers=BAD_USER_HEADERS,
            )

        user_id = UUID(jwt.sub)
        query = select(users.User).where(users.User.user_id == user_id)

        user = session.exec(query).one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers=BAD_USER_HEADERS,
            )

        if self.required_role and self.required_role not in [role.role_name for role in user.roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
                headers=BAD_USER_HEADERS,
            )

        response.headers["X-Auth-User-ID"] = user.user_id.hex
        response.headers["X-Auth-Roles"] = ",".join(role.role_name for role in user.roles)

        return user


class UserInfoResponse(BaseModel):
    """Response model for user info endpoint."""

    user_id: str
    user_name: str
    roles: list[str]


@app.get(
    "/user/me",
    summary="Get current user info",
)
def get_current_user_info(
    user: Annotated[users.User, Depends(CheckRole(None))],
    session: Annotated[Session, Depends(get_session)],
) -> UserInfoResponse:
    """Endpoint to get current user info."""
    query = select(users.User).where(users.User.user_name == "admin")
    user = session.exec(query).one()
    return UserInfoResponse(
        user_id=str(user.user_id),
        user_name=user.user_name,
        roles=[role.role_name for role in user.roles],
    )
