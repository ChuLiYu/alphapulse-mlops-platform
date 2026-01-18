"""
Authentication and authorization utilities for AlphaPulse.

This module provides JWT token handling, password hashing, and permission checking
for securing API endpoints and data access.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from alphapulse.api.database import get_db
from alphapulse.api.models_user import APIKey, AuditLog, Role, User, UserRole

# Security configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY", "your-secret-key-for-development-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security
security = HTTPBearer()


class AuthService:
    """Service for authentication and authorization operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password for storage."""
        return pwd_context.hash(password)

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
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_current_user(self, token: str) -> Optional[User]:
        """Get the current user from a JWT token."""
        payload = self.verify_token(token)
        if payload is None:
            return None

        username: str = payload.get("sub")
        if username is None:
            return None

        user = self.db.query(User).filter(User.username == username).first()
        if user is None or not user.is_active:
            return None

        return user

    def verify_api_key(self, api_key: str) -> Optional[User]:
        """Verify an API key and return the associated user."""
        # In production, we would hash the API key before comparing
        # For simplicity, we're doing direct comparison here
        api_key_record = (
            self.db.query(APIKey)
            .filter(APIKey.key == api_key, APIKey.is_active == True)
            .first()
        )

        if not api_key_record:
            return None

        if api_key_record.is_expired():
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
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that bypasses actual authentication.
    Returns a dummy admin user to allow full access without login.
    """
    # Create a dummy admin user structure
    # We use a mock object or fetch the actual admin if it exists
    # For safety/simplicity in this "no-auth" mode, we return a constructed User object
    # This avoids database lookups if the DB is empty or locked
    from datetime import datetime

    return User(
        id=1,
        username="admin",
        email="admin@alphapulse.local",
        is_active=True,
        is_superuser=True,
        hashed_password="dummy_hash_bypass",
        created_at=datetime.utcnow(),
    )


def get_current_user_from_api_key(
    api_key: Optional[str] = None, db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency to get current user from API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required"
        )

    auth_service = AuthService(db)
    user = auth_service.verify_api_key(api_key)

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
