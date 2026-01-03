"""Models for users and roles in the Digital Twin Platform."""

from uuid import UUID, uuid7

from sqlmodel import Field as SQLField
from sqlmodel import Relationship, SQLModel


class UserRoleLink(SQLModel, table=True):
    """Link model representing the association between users and roles."""

    user_id: UUID = SQLField(title="User ID", primary_key=True, foreign_key="user.user_id")
    role_id: UUID = SQLField(title="Role ID", primary_key=True, foreign_key="role.role_id")


class User(SQLModel, table=True):
    """User model representing a user in the system."""

    user_id: UUID = SQLField(
        title="User ID",
        default_factory=uuid7,
        primary_key=True,
    )
    user_name: str = SQLField(title="User name", unique=True, index=True)
    password_hash: str = SQLField(title="Password hash")

    roles: list["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)


class Role(SQLModel, table=True):
    """Role model representing a role assigned to a user.

    A user has role `r` if `r in user.roles`.

    Note that since API access is controlled using role names, role names should
    be unique and immutable.
    """

    role_id: UUID = SQLField(
        title="Role ID",
        default_factory=uuid7,
        primary_key=True,
    )
    role_name: str = SQLField(title="Role name", unique=True, index=True, allow_mutation=False)

    users: list[User] = Relationship(back_populates="roles", link_model=UserRoleLink)
