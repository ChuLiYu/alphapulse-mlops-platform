"""
Authentication and authorization API endpoints.

This module provides endpoints for:
- User registration and login
- JWT token management
- API key management
- User and role management
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from alphapulse.api.database import get_db
from alphapulse.api.models_user import APIKey, Role, User, UserRole
from alphapulse.security.auth import (
    PERMISSIONS,
    AuthService,
    create_default_roles,
    get_current_user_from_token,
    require_permission,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


# Pydantic models
class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data model."""

    username: Optional[str] = None


class UserCreate(BaseModel):
    """User creation request model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""

    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class APIKeyCreate(BaseModel):
    """API key creation request model."""

    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response model."""

    id: int
    name: str
    key: str  # Only shown on creation
    scopes: List[str]
    expires_at: Optional[datetime]
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    """Role creation request model."""

    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


class RoleResponse(BaseModel):
    """Role response model."""

    id: int
    name: str
    description: Optional[str]
    permissions: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RoleSwitchRequest(BaseModel):
    """Request model for switching user role (Simulation)."""
    target_role: str


class RoleSwitchResponse(BaseModel):
    """Response model for role switching."""
    status: str
    permissions: List[str]


# Authentication endpoints
@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    auth_service = AuthService(db)

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = auth_service.get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Assign default role (viewer)
    viewer_role = db.query(Role).filter(Role.name == "viewer").first()
    if viewer_role:
        user_role = UserRole(user_id=user.id, role_id=viewer_role.id)
        db.add(user_role)
        db.commit()

    # Log audit event
    auth_service.log_audit_event(
        user_id=user.id,
        action="user_registered",
        resource_type="user",
        resource_id=str(user.id),
        details={"username": user.username, "email": user.email},
    )

    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest, request: Request, db: Session = Depends(get_db)
):
    """Login user and return JWT tokens."""
    auth_service = AuthService(db)

    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = auth_service.create_access_token(data={"sub": user.username})
    refresh_token = auth_service.create_refresh_token(data={"sub": user.username})

    # Log audit event
    auth_service.log_audit_event(
        user_id=user.id,
        action="user_login",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"login_method": "password"},
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,  # 30 minutes in seconds
    )


@router.post("/switch-role", response_model=RoleSwitchResponse)
async def switch_role(
    role_data: RoleSwitchRequest,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Simulate switching roles (Dev/Demo only).
    
    This is used for frontend SecOps demonstrations to show how the UI adapts
    to different permission levels.
    """
    # Simple logic mapping for demo
    permissions = []
    if role_data.target_role == "admin":
        permissions = list(PERMISSIONS.keys())
    elif role_data.target_role == "trader":
        permissions = ["signal:view", "trade:execute"]
    else:
        permissions = ["signal:view"]
        
    return RoleSwitchResponse(
        status="switched",
        permissions=permissions
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db)

    payload = auth_service.verify_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    access_token = auth_service.create_access_token(data={"sub": user.username})
    new_refresh_token = auth_service.create_refresh_token(data={"sub": user.username})

    return Token(
        access_token=access_token, refresh_token=new_refresh_token, expires_in=30 * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_user_from_token)):
    """Get current user information."""
    return current_user


# API Key management endpoints
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """Create a new API key for the current user."""
    auth_service = AuthService(db)

    # Generate API key
    raw_key = APIKey.generate_key()

    # Calculate expiration
    expires_at = None
    if api_key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)

    # Create API key record
    api_key = APIKey(
        user_id=current_user.id,
        key=raw_key,  # In production, hash this key
        name=api_key_data.name,
        scopes=str(api_key_data.scopes),  # Store as JSON string
        expires_at=expires_at,
        is_active=True,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Log audit event
    auth_service.log_audit_event(
        user_id=current_user.id,
        action="api_key_created",
        resource_type="api_key",
        resource_id=str(api_key.id),
        details={"name": api_key.name, "scopes": api_key_data.scopes},
    )

    # Return response with the raw key (only shown once)
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        scopes=api_key_data.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """List API keys for the current user."""
    api_keys = (
        db.query(APIKey)
        .filter(APIKey.user_id == current_user.id, APIKey.is_active == True)
        .all()
    )

    # Don't expose the actual key values in list view
    response = []
    for api_key in api_keys:
        import json

        scopes = json.loads(api_key.scopes) if api_key.scopes else []
        response.append(
            APIKeyResponse(
                id=api_key.id,
                name=api_key.name,
                key=(
                    "***" + api_key.key[-4:] if api_key.key else "***"
                ),  # Show only last 4 chars
                scopes=scopes,
                expires_at=api_key.expires_at,
                created_at=api_key.created_at,
                last_used_at=api_key.last_used_at,
                is_active=api_key.is_active,
            )
        )

    return response


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """Revoke (deactivate) an API key."""
    auth_service = AuthService(db)

    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == api_key_id, APIKey.user_id == current_user.id)
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    api_key.is_active = False
    db.commit()

    # Log audit event
    auth_service.log_audit_event(
        user_id=current_user.id,
        action="api_key_revoked",
        resource_type="api_key",
        resource_id=str(api_key.id),
        details={"name": api_key.name},
    )

    return {"message": "API key revoked successfully"}


# Role management endpoints (admin only)
@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(require_permission("system:admin")),
    db: Session = Depends(get_db),
):
    """List all roles (admin only)."""
    roles = db.query(Role).all()

    response = []
    for role in roles:
        import json

        permissions = json.loads(role.permissions) if role.permissions else []
        response.append(
            RoleResponse(
                id=role.id,
                name=role.name,
                description=role.description,
                permissions=permissions,
                created_at=role.created_at,
            )
        )

    return response


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_permission("system:admin")),
    db: Session = Depends(get_db),
):
    """Create a new role (admin only)."""
    auth_service = AuthService(db)

    # Check if role already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists"
        )

    # Validate permissions
    invalid_permissions = []
    for permission in role_data.permissions:
        if permission not in PERMISSIONS:
            invalid_permissions.append(permission)

    if invalid_permissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permissions: {invalid_permissions}",
        )

    # Create role
    import json

    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=json.dumps(role_data.permissions),
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    # Log audit event
    auth_service.log_audit_event(
        user_id=current_user.id,
        action="role_created",
        resource_type="role",
        resource_id=str(role.id),
        details={"name": role.name, "permissions": role_data.permissions},
    )

    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=role_data.permissions,
        created_at=role.created_at,
    )


@router.get("/permissions")
async def list_permissions():
    """List all available permissions."""
    return PERMISSIONS


# System endpoints
@router.post("/initialize")
async def initialize_system(
    current_user: User = Depends(require_permission("system:admin")),
    db: Session = Depends(get_db),
):
    """Initialize system with default roles and admin user."""
    auth_service = AuthService(db)

    # Create default roles
    create_default_roles(db)

    # Check if admin user exists
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        # Create admin user
        hashed_password = auth_service.get_password_hash("admin123")
        admin_user = User(
            username="admin",
            email="admin@alphapulse.local",
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        # Assign admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.add(user_role)
            db.commit()

    return {
        "message": "System initialized successfully",
        "admin_username": "admin",
        "default_password": "admin123",
        "warning": "Change the admin password immediately!",
    }
