"""Core API server for the DTP backend."""

from contextlib import asynccontextmanager

from dotenv import find_dotenv
from fastapi import FastAPI, Request
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


@app.get("/health", summary="Health check endpoint", response_class=PlainTextResponse)
def health_check() -> str:
    """Health check endpoint to verify that the service is running.

    Returns:
        A simple "OK" string.
    """
    return "OK"
