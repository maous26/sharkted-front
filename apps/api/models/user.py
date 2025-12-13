"""
Router Users - Gestion des utilisateurs et authentification
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid

from database import get_db, User, PlanType, Outcome
from config import settings

router = APIRouter()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

# ============= SCHEMAS =============

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str]
    plan: str
    preferences: Optional[dict]
    discord_webhook: Optional[str]
    email_alerts: bool
    total_deals_viewed: int
    total_deals_bought: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    discord_webhook: Optional[str] = None
    email_alerts: Optional[bool] = None
    preferences: Optional[dict] = None

class UserPreferences(BaseModel):
    min_margin: Optional[float] = 20
    categories: Optional[List[str]] = []
    brands: Optional[List[str]] = []
    sizes: Optional[List[str]] = []
    risk_profile: Optional[str] = "balanced"
    alert_threshold: Optional[int] = 70

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None

# ============= HELPERS =============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    query = select(User).where(User.id == uuid.UUID(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Compte désactivé")
    
    return user

# ============= ENDPOINTS =============

@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Inscription d'un nouvel utilisateur
    """
    # Check if email exists
    query = select(User).where(User.email == user_data.email.lower())
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Un compte avec cet email existe déjà"
        )
    
    # Create user
    user = User(
        email=user_data.email.lower(),
        hashed_password=get_password_hash(user_data.password),
        name=user_data.name,
        plan=PlanType.FREE,
        preferences={
            "min_margin": 20,
            "categories": [],
            "brands": [],
            "sizes": [],
            "risk_profile": "balanced",
            "alert_threshold": 70
        }
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            plan=user.plan.value,
            preferences=user.preferences,
            discord_webhook=user.discord_webhook,
            email_alerts=user.email_alerts,
            total_deals_viewed=user.total_deals_viewed,
            total_deals_bought=user.total_deals_bought,
            created_at=user.created_at
        )
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Connexion utilisateur
    """
    query = select(User).where(User.email == form_data.username.lower())
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Compte désactivé")
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Generate token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            plan=user.plan.value,
            preferences=user.preferences,
            discord_webhook=user.discord_webhook,
            email_alerts=user.email_alerts,
            total_deals_viewed=user.total_deals_viewed,
            total_deals_bought=user.total_deals_bought,
            created_at=user.created_at
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les informations de l'utilisateur connecté
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        plan=current_user.plan.value,
        preferences=current_user.preferences,
        discord_webhook=current_user.discord_webhook,
        email_alerts=current_user.email_alerts,
        total_deals_viewed=current_user.total_deals_viewed,
        total_deals_bought=current_user.total_deals_bought,
        created_at=current_user.created_at
    )


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Met à jour les informations de l'utilisateur connecté
    """
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        plan=current_user.plan.value,
        preferences=current_user.preferences,
        discord_webhook=current_user.discord_webhook,
        email_alerts=current_user.email_alerts,
        total_deals_viewed=current_user.total_deals_viewed,
        total_deals_bought=current_user.total_deals_bought,
        created_at=current_user.created_at
    )


@router.put("/me/preferences", response_model=UserResponse)
async def update_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Met à jour les préférences de l'utilisateur
    """
    current_user.preferences = preferences.model_dump()
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        plan=current_user.plan.value,
        preferences=current_user.preferences,
        discord_webhook=current_user.discord_webhook,
        email_alerts=current_user.email_alerts,
        total_deals_viewed=current_user.total_deals_viewed,
        total_deals_bought=current_user.total_deals_bought,
        created_at=current_user.created_at
    )


@router.get("/me/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupère les statistiques de l'utilisateur
    """
    # Outcomes stats
    from sqlalchemy import func
    from database import Outcome, ActionType
    
    # Total bought
    bought_query = select(func.count(Outcome.id)).where(
        Outcome.user_id == current_user.id,
        Outcome.action == ActionType.BOUGHT
    )
    bought_result = await db.execute(bought_query)
    total_bought = bought_result.scalar() or 0
    
    # Total sold
    sold_query = select(func.count(Outcome.id)).where(
        Outcome.user_id == current_user.id,
        Outcome.sold == True
    )
    sold_result = await db.execute(sold_query)
    total_sold = sold_result.scalar() or 0
    
    # Total profit
    profit_query = select(func.sum(Outcome.actual_margin_euro)).where(
        Outcome.user_id == current_user.id,
        Outcome.sold == True
    )
    profit_result = await db.execute(profit_query)
    total_profit = profit_result.scalar() or 0
    
    # Average margin
    avg_margin_query = select(func.avg(Outcome.actual_margin_percent)).where(
        Outcome.user_id == current_user.id,
        Outcome.sold == True
    )
    avg_margin_result = await db.execute(avg_margin_query)
    avg_margin = avg_margin_result.scalar() or 0
    
    # Average days to sell
    avg_days_query = select(func.avg(Outcome.days_to_sell)).where(
        Outcome.user_id == current_user.id,
        Outcome.sold == True
    )
    avg_days_result = await db.execute(avg_days_query)
    avg_days = avg_days_result.scalar() or 0
    
    return {
        "total_deals_viewed": current_user.total_deals_viewed,
        "total_bought": total_bought,
        "total_sold": total_sold,
        "pending_sales": total_bought - total_sold,
        "total_profit_euro": round(total_profit, 2),
        "average_margin_percent": round(avg_margin, 1) if avg_margin else 0,
        "average_days_to_sell": round(avg_days, 1) if avg_days else 0,
        "success_rate": round((total_sold / total_bought * 100), 1) if total_bought > 0 else 0
    }