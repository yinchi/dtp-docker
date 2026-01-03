"""Core API server for the DTP backend."""

from contextlib import asynccontextmanager

from dotenv import find_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import Field
from pydantic_settings import BaseSettings


class DTPSettings(BaseSettings):
    """Settings for the DTP Authentication service."""

    host: str = Field(min_length=1, default="http://dtp-docker:8000")
    root_path: str = Field(default="/api")

    class Config:
        """Configuration for Pydantic Settings."""

        env_file = find_dotenv(".env")
        env_file_encoding = "utf-8"
        env_prefix = "DTP_API_"
        extra = "ignore"  # Ignore extra environment variables


dtp_host = DTPSettings().host


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for the FastAPI application."""
    yield
    # Add any shutdown logic here if needed


app = FastAPI(
    root_path=DTPSettings().root_path,
    title="Digital Twin Platform: Core API",
    lifespan=lifespan,
    # docs_url=None,  # Disable Swagger UI
    # redoc_url=None,  # Disable ReDoc UI
    swagger_ui_parameters={
        # "supportedSubmitMethods": [],  # Disable "Try it out" button
    },
)


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


@app.get("/health", summary="Health check endpoint", response_class=PlainTextResponse)
def health_check() -> str:
    """Health check endpoint to verify that the service is running.

    Returns:
        A simple "OK" string.
    """
    return "OK"
