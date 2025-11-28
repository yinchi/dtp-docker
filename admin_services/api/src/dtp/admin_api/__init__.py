"""Digital Twin Platform: Admin API."""

import sys
from importlib.metadata import version
from typing import Annotated

import docker
import fastapi.cli
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for Admin API."""

    # On the host machine (running natively), `DTP_ADMIN_API_ROOT_PATH` should be unset.
    # Inside Docker, it is set in `docker-compose.yml` (e.g. "/api/admin").
    root_path: str = ""

    # Set to True to hide API documentation (e.g. in production settings)
    hide_documentation: bool = False

    class Config:
        """Pydantic settings configuration."""

        env_prefix = "DTP_ADMIN_API_"


# Configure documentation settings based on environment variable
documentation_settings = {}
if Settings().hide_documentation:
    documentation_settings = {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }

app = FastAPI(
    title="Digital Twin Platform: Admin API",
    description="""\
Admin API for platform management and monitoring.

### Authentication
The Admin API checks the `x-auth-user` header to verify that the request is made by an authorized
admin user.  This should be set by the upstream reverse proxy (e.g. Traefik) after validating the
user's credentials.

In the testing environment, the following admin user is available:
- Username: `admin`
- Password: `testpassword`

### Example (Basic Auth)

```bash
echo &&
curl -D - -X 'GET' \\
  'https://dtp-docker.example.com/api/admin/me' \\
  -H 'accept: application/json, ' \\
  -H "authorization: Basic $(echo -n 'admin:testpassword' | base64)" &&
echo
```""",
    version=version("dtp.admin_api"),
    license_info={
        "name": "MIT License",
        "identifier": "MIT",
    },
    **documentation_settings,
)


async def check_admin_user(
    request: Request,
) -> None:
    """Admin user authentication."""
    # Placeholder: check against list of admin users
    # In production, this list should be fetched from database or secure storage
    admin_users = {"admin"}

    # Since BasicAuth already checks password, we only verify username here
    user = request.headers.get("x-auth-user", None)
    if not user or user not in admin_users:
        raise HTTPException(status_code=401, detail="Unauthorized user")

    return user


@app.get(
    "/health",
    summary="Health check",
    response_class=PlainTextResponse,
)
async def health_check() -> str:
    """Health check endpoint."""
    return "OK"


@app.get(
    "/me",
    summary="Get current user",
)
async def root(
    x_auth_user: Annotated[str, Depends(check_admin_user)] = None,
):
    """Get current admin user info.

    Currently, we only return the username from the `x-auth-user` header.
    In the future, additional user details can be fetched from a database.
    """
    return {
        "x_auth_user": x_auth_user,
    }


@app.get(
    "/docker/containers",
    summary="Get info on Docker containers",
    tags=["Docker Compose"],
)
async def get_containers(
    _x_auth_user: Annotated[str, Depends(check_admin_user)] = None,
):
    """Get info on Docker containers.

    This endpoint retrieves information about Docker containers managed by the Docker Digital Twin
    Platform.
    """
    client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
    return {
        container.name: {
            "status": container.status,
            "service": container.labels.get("com.docker.compose.service", None),
            "dtp_labels": {k: v for k, v in container.labels.items() if k.startswith("dtp.")},
        }
        for container in client.containers.list()
        if "dtp-docker" in container.labels.get("com.docker.compose.project", "")
    }


def main() -> str:
    """Main entry point for FastAPI CLI."""
    # Set up argv for FastAPI CLI
    settings = Settings()
    print(f"Starting DTP Admin API with settings: '{settings}'")

    sys.argv = [
        sys.argv[0],
        "dev",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "-e",
        "dtp.admin_api:app",
        "--reload",
        "--root-path",
        settings.root_path,
    ]
    # Call FastAPI CLI main function with the modified argv
    fastapi.cli.main()
