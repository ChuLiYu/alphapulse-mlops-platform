"""
User authentication models for AlphaPulse.

This module defines SQLAlchemy models for user authentication and authorization,
including API key management and role-based access control.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from alphapulse.api.database import Base


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Primary key
        username: Unique username for login
        email: User email address
        hashed_password: BCrypt hashed password
        is_active: Whether the user account is active
        is_superuser: Whether the user has superuser privileges
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        api_keys: Relationship to API keys
        roles: Relationship to user roles
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[UserRole.user_id]",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class APIKey(Base):
    """
    API key model for programmatic access.

    Attributes:
        id: Primary key
        user_id: Foreign key to user
        key: API key (hashed for storage)
        name: Descriptive name for the API key
        scopes: JSON string of allowed scopes
        expires_at: When the API key expires (null for no expiration)
        last_used_at: When the API key was last used
        created_at: Timestamp when API key was created
        is_active: Whether the API key is active
        user: Relationship to user
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String(64), unique=True, index=True, nullable=False)  # Hashed key
    name = Column(String(100), nullable=False)
    scopes = Column(Text, default="[]")  # JSON array of scopes
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name='{self.name}', user_id={self.user_id})>"

    @staticmethod
    def generate_key() -> str:
        """Generate a secure random API key."""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(32))

    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class Role(Base):
    """
    Role model for role-based access control.

    Attributes:
        id: Primary key
        name: Role name (e.g., 'admin', 'viewer', 'trader')
        description: Role description
        permissions: JSON string of permissions
        created_at: Timestamp when role was created
    """

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255))
    permissions = Column(Text, default="[]")  # JSON array of permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_roles = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


class UserRole(Base):
    """
    Junction table for user-role many-to-many relationship.

    Attributes:
        id: Primary key
        user_id: Foreign key to user
        role_id: Foreign key to role
        assigned_at: Timestamp when role was assigned
        assigned_by: User who assigned the role
        user: Relationship to user
        role: Relationship to role
    """

    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return (
            f"<UserRole(id={self.id}, user_id={self.user_id}, role_id={self.role_id})>"
        )


class AuditLog(Base):
    """
    Audit log for security events and user actions.

    Attributes:
        id: Primary key
        user_id: Foreign key to user (nullable for system events)
        action: Action performed (e.g., 'login', 'api_call', 'data_access')
        resource_type: Type of resource accessed
        resource_id: ID of resource accessed
        ip_address: IP address of requester
        user_agent: User agent string
        details: JSON string with additional details
        created_at: Timestamp when event occurred
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    ip_address = Column(String(45))  # Supports IPv6
    user_agent = Column(Text)
    details = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"
        )
