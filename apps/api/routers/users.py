"""Users router - endpoints for user management and authentication."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field

from database import get_db, PlanType
from models import User
from dependencies import get_current_user, create_access_token
from utils.helpers import hash_password, verify_password

router = APIRouter()


# Pydantic schemas
class UserCreate(BaseModel):
    """User registration schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update schema."""
    name: Optional[str] = None
    discord_webhook: Optional[str] = None
    email_alerts: Optional[bool] = None
    preferences: Optional[dict] = None


class UserPreferences(BaseModel):
    """User preferences schema."""
    min_margin: Optional[float] = Field(20, ge=0)
    categories: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    risk_profile: Optional[str] = Field("balanced", pattern="^(conservative|balanced|aggressive)$")
    alert_threshold: Optional[int] = Field(70, ge=0, le=100)


class UserResponse(BaseModel):
    """User response schema."""
    id: UUID
    email: str
    name: Optional[str]
    plan: str
    preferences: Optional[dict]
    discord_webhook: Optional[str]
    email_alerts: bool
    is_active: bool
    is_verified: bool
    total_deals_viewed: int
    total_deals_bought: int
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


def get_plan_value(plan) -> str:
    """Get string value from plan (handles both enum and string)."""
    if hasattr(plan, 'value'):
        return plan.value
    return str(plan)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password),
        name=user_data.name,
        plan=PlanType.FREE,
        is_active=True,
        preferences={
            "min_margin": 20,
            "categories": [],
            "brands": [],
            "sizes": [],
            "risk_profile": "balanced",
            "alert_threshold": 70,
        },
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            plan=get_plan_value(user.plan),
            preferences=user.preferences,
            discord_webhook=user.discord_webhook,
            email_alerts=user.email_alerts,
            is_active=user.is_active,
            is_verified=user.is_verified,
            total_deals_viewed=user.total_deals_viewed,
            total_deals_bought=user.total_deals_bought,
            created_at=user.created_at,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return token."""

    result = await db.execute(select(User).where(User.email == credentials.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            plan=get_plan_value(user.plan),
            preferences=user.preferences,
            discord_webhook=user.discord_webhook,
            email_alerts=user.email_alerts,
            is_active=user.is_active,
            is_verified=user.is_verified,
            total_deals_viewed=user.total_deals_viewed,
            total_deals_bought=user.total_deals_bought,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
):
    """Get current user information."""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        plan=get_plan_value(user.plan),
        preferences=user.preferences,
        discord_webhook=user.discord_webhook,
        email_alerts=user.email_alerts,
        is_active=user.is_active,
        is_verified=user.is_verified,
        total_deals_viewed=user.total_deals_viewed,
        total_deals_bought=user.total_deals_bought,
        created_at=user.created_at,
    )


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user information."""

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        plan=get_plan_value(user.plan),
        preferences=user.preferences,
        discord_webhook=user.discord_webhook,
        email_alerts=user.email_alerts,
        is_active=user.is_active,
        is_verified=user.is_verified,
        total_deals_viewed=user.total_deals_viewed,
        total_deals_bought=user.total_deals_bought,
        created_at=user.created_at,
    )


@router.put("/me/preferences", response_model=UserResponse)
async def update_preferences(
    preferences: UserPreferences,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences."""

    # Merge with existing preferences
    current_prefs = user.preferences or {}
    new_prefs = preferences.model_dump(exclude_unset=True)
    current_prefs.update(new_prefs)

    user.preferences = current_prefs
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        plan=get_plan_value(user.plan),
        preferences=user.preferences,
        discord_webhook=user.discord_webhook,
        email_alerts=user.email_alerts,
        is_active=user.is_active,
        is_verified=user.is_verified,
        total_deals_viewed=user.total_deals_viewed,
        total_deals_bought=user.total_deals_bought,
        created_at=user.created_at,
    )
