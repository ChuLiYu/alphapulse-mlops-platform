"""
Authentication and authorization utilities for AlphaPulse.

This module provides JWT token handling, password hashing, and permission checking
for securing API endpoints and data access.
"""

import os
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Security, Depends, HTTPException, status
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
    SecurityScopes,
)
import jwt
from jwt.exceptions import PyJWTError
import bcrypt
from sqlalchemy import update
from sqlalchemy.orm import Session

from alphapulse.api.database import get_db
from alphapulse.api.models_user import APIKey, AuditLog, RefreshToken, Role, User, UserRole


# Security configuration
def signing_key():
    key = os.getenv("SECRET_KEY", "")
    if len(key) < 32 or key == "your-secret-key-for-development-change-in-production":
        raise RuntimeError("Configure SECRET_KEY with at least 32 random characters")
    return key


def hash_api_key(raw_key):
    # Generated keys contain ~190 bits of entropy; SHA-256 fits the existing column.
    return hashlib.sha256(raw_key.encode()).hexdigest()


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# HTTP Bearer security
security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthService:
    """Service for authentication and authorization operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        try:
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except ValueError:
            return False

    def get_password_hash(self, password: str) -> str:
        """Hash a password for storage."""
        if len(password.encode()) > 72:
            raise HTTPException(
                status_code=400, detail="Password exceeds 72 UTF-8 bytes"
            )
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, signing_key(), algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a refresh JWT with a persisted one-time-use identifier."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jti = secrets.token_urlsafe(32)
        to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
        encoded_jwt = jwt.encode(to_encode, signing_key(), algorithm=ALGORITHM)
        user = self.db.query(User).filter(User.username == data.get("sub")).first()
        if user is None:
            raise ValueError("Cannot issue refresh token for an unknown user")
        self.db.add(
            RefreshToken(
                jti_digest=hashlib.sha256(jti.encode()).hexdigest(),
                user_id=user.id,
                expires_at=expire,
            )
        )
        return encoded_jwt

    def consume_refresh_token(self, payload: Dict[str, Any], user: User) -> bool:
        """Atomically consume a refresh token so it cannot be replayed."""
        jti = payload.get("jti")
        if not isinstance(jti, str) or not 1 <= len(jti) <= 128:
            return False
        now = datetime.utcnow()
        result = self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.jti_digest == hashlib.sha256(jti.encode()).hexdigest(),
                RefreshToken.user_id == user.id,
                RefreshToken.consumed_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .values(consumed_at=now)
        )
        return result.rowcount == 1

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                signing_key(),
                algorithms=[ALGORITHM],
                options={"require": ["exp", "sub", "type"]},
            )
            return payload
        except PyJWTError:
            return None

    def get_current_user(self, token: str) -> Optional[User]:
        """Get the current user from a JWT token."""
        payload = self.verify_token(token)
        if payload is None or payload.get("type") != "access":
            return None

        username: str = payload.get("sub")
        if username is None:
            return None

        user = self.db.query(User).filter(User.username == username).first()
        if user is None or not user.is_active:
            return None

        return user

    def verify_api_key(self, api_key: str, required_scopes=()) -> Optional[User]:
        """Verify an API key and return the associated user."""
        api_key_record = (
            self.db.query(APIKey)
            .filter(APIKey.key == hash_api_key(api_key), APIKey.is_active == True)
            .first()
        )

        if not api_key_record:
            return None

        if api_key_record.is_expired() or not api_key_record.user.is_active:
            return None

        try:
            scopes = json.loads(api_key_record.scopes)
            if not isinstance(scopes, list) or any(
                scope not in scopes
                or not self.check_permission(api_key_record.user, scope)
                for scope in required_scopes
            ):
                return None
        except (ValueError, TypeError):
            return None

        # Update last used timestamp
        api_key_record.last_used_at = datetime.utcnow()
        self.db.commit()

        return api_key_record.user

    def check_permission(self, user: User, permission: str) -> bool:
        """Check if a user has a specific permission."""
        if user.is_superuser:
            return True

        # Get all roles for the user
        user_roles = self.db.query(UserRole).filter(UserRole.user_id == user.id).all()
        role_ids = [ur.role_id for ur in user_roles]

        if not role_ids:
            return False

        # Get all permissions from user's roles
        roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()

        for role in roles:
            # permissions is stored as JSON string, parse it
            import json

            try:
                permissions = json.loads(role.permissions)
                if permission in permissions:
                    return True
            except (json.JSONDecodeError, TypeError):
                continue

        return False

    def log_audit_event(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log an audit event."""
        import json

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details) if details else None,
        )

        self.db.add(audit_log)
        self.db.commit()


# FastAPI dependencies
def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid access token and an active persisted user."""
    user = None
    if credentials is not None:
        user = AuthService(db).get_current_user(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_from_api_key(
    security_scopes: SecurityScopes,
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to get current user from API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required"
        )

    auth_service = AuthService(db)
    user = auth_service.verify_api_key(api_key, security_scopes.scopes)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return user


def require_permission(permission: str):
    """Decorator-like function to require a specific permission."""

    def permission_dependency(
        current_user: User = Depends(get_current_user_from_token),
        db: Session = Depends(get_db),
    ) -> User:
        auth_service = AuthService(db)

        if not auth_service.check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )

        return current_user

    return permission_dependency


# Common permissions
PERMISSIONS = {
    # Data access
    "data:read": "Read data (prices, indicators)",
    "data:write": "Write data (prices, indicators)",
    "data:delete": "Delete data",
    # User management
    "users:read": "Read user information",
    "users:write": "Create/update users",
    "users:delete": "Delete users",
    # API key management
    "apikeys:read": "Read API keys",
    "apikeys:write": "Create/update API keys",
    "apikeys:delete": "Delete API keys",
    # System administration
    "system:monitor": "Monitor system health",
    "system:configure": "Configure system settings",
    "system:admin": "Full system administration",
    # Trading operations
    "trading:read": "Read trading signals",
    "trading:write": "Create trading signals",
    "trading:execute": "Execute trades",
}


def create_default_roles(db: Session):
    """Create default roles with permissions."""
    import json

    default_roles = [
        {
            "name": "viewer",
            "description": "Read-only access to data",
            "permissions": ["data:read", "trading:read"],
        },
        {
            "name": "trader",
            "description": "Trading operations",
            "permissions": [
                "data:read",
                "trading:read",
                "trading:write",
                "trading:execute",
            ],
        },
        {
            "name": "data_scientist",
            "description": "Data science and analysis",
            "permissions": ["data:read", "data:write", "system:monitor"],
        },
        {
            "name": "admin",
            "description": "System administrator",
            "permissions": list(PERMISSIONS.keys()),
        },
    ]

    for role_data in default_roles:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=json.dumps(role_data["permissions"]),
            )
            db.add(role)

    db.commit()
