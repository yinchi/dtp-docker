"""Common data models used across the DTP application."""

from dtp.common import fastapi_json_example
from pydantic import BaseModel


class MeResponse(BaseModel):
    """Result of the /me endpoint containing user information."""

    x_auth_user: str


me_example = fastapi_json_example(MeResponse(x_auth_user="example_user"))


class DockerContainerInfo(BaseModel):
    """Information about a Docker container."""

    status: str
    service: str | None
    dtp_labels: dict[str, str]


class DockerContainersInfoResponse(BaseModel):
    """Response model for Docker containers info endpoint."""

    containers: dict[str, DockerContainerInfo]


docker_container_info_example = fastapi_json_example(
    DockerContainersInfoResponse(
        containers={
            "web": DockerContainerInfo(
                status="running",
                service="web",
                dtp_labels={"dtp.example": "value"},
            )
        }
    )
)
