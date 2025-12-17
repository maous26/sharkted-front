"""
Router Favorites - Gestion des deals favoris/trackes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
from loguru import logger

from database import get_db, Favorite, Deal, User
from routers.users import get_current_user

router = APIRouter()


# ============= SCHEMAS =============

class FavoriteCreate(BaseModel):
    deal_id: int
    notes: Optional[str] = None


class FavoriteResponse(BaseModel):
    id: int
    user_id: str
    deal_id: str
    notes: Optional[str]
    created_at: datetime
    deal: Optional[dict] = None

    class Config:
        from_attributes = True


class FavoritesListResponse(BaseModel):
    favorites: List[FavoriteResponse]
    total: int
    page: int
    per_page: int
    pages: int


class FavoriteIdsResponse(BaseModel):
    deal_ids: List[int]


# ============= ENDPOINTS =============

@router.get("", response_model=FavoritesListResponse)
async def list_favorites(
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Liste les favoris d'un utilisateur avec pagination."""

    # Use user_id from query if provided (for admin), otherwise current user
    target_user_id = int(user_id) if user_id else current_user.id

    # Count total
    count_query = select(Favorite).where(Favorite.user_id == target_user_id)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # Fetch favorites with deals
    offset = (page - 1) * per_page
    query = (
        select(Favorite)
        .where(Favorite.user_id == target_user_id)
        .options(selectinload(Favorite.deal))
        .order_by(Favorite.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )

    result = await db.execute(query)
    favorites = result.scalars().all()

    # Format response
    favorites_list = []
    for fav in favorites:
        deal_data = None
        if fav.deal:
            deal = fav.deal
            deal_data = {
                "id": str(deal.id),
                "title": deal.title,
                "product_name": deal.title,
                "brand": deal.brand or "",
                "price": float(deal.price) if deal.price else 0,
                "original_price": float(deal.original_price) if deal.original_price else None,
                "discount_percent": float(deal.discount_percent) if deal.discount_percent else None,
                "url": deal.url,
                "image_url": deal.image_url,
                "source": deal.source,
                "first_seen_at": deal.first_seen_at.isoformat() if deal.first_seen_at else None,
            }

        favorites_list.append(FavoriteResponse(
            id=fav.id,
            user_id=str(fav.user_id),
            deal_id=str(fav.deal_id),
            notes=fav.notes,
            created_at=fav.created_at,
            deal=deal_data
        ))

    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return FavoritesListResponse(
        favorites=favorites_list,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )


@router.get("/ids", response_model=FavoriteIdsResponse)
async def get_favorite_ids(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retourne la liste des IDs de deals favoris de l'utilisateur."""

    target_user_id = int(user_id) if user_id else current_user.id

    query = select(Favorite.deal_id).where(Favorite.user_id == target_user_id)
    result = await db.execute(query)
    deal_ids = [row[0] for row in result.all()]

    return FavoriteIdsResponse(deal_ids=deal_ids)


@router.post("")
async def add_favorite(
    data: FavoriteCreate,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ajoute un deal aux favoris."""

    target_user_id = int(user_id) if user_id else current_user.id

    # Check deal exists
    deal_result = await db.execute(select(Deal).where(Deal.id == data.deal_id))
    target_deal = deal_result.scalar_one_or_none()

    if not target_deal:
        raise HTTPException(status_code=404, detail="Deal non trouve")

    # Check if already favorited
    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == target_user_id,
            Favorite.deal_id == target_deal.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Deal deja en favoris")

    # Create favorite
    favorite = Favorite(
        user_id=target_user_id,
        deal_id=target_deal.id,
        notes=data.notes
    )
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    logger.info(f"Favorite added: user={target_user_id}, deal={target_deal.id}")

    return {"success": True, "id": favorite.id}


@router.delete("/{deal_id}")
async def remove_favorite(
    deal_id: int,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retire un deal des favoris."""

    target_user_id = int(user_id) if user_id else current_user.id

    # Delete favorite
    result = await db.execute(
        delete(Favorite).where(
            Favorite.user_id == target_user_id,
            Favorite.deal_id == deal_id
        )
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Favori non trouve")

    logger.info(f"Favorite removed: user={target_user_id}, deal={deal_id}")

    return {"success": True}


@router.get("/check/{deal_id}")
async def check_favorite(
    deal_id: int,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verifie si un deal est en favoris."""

    target_user_id = int(user_id) if user_id else current_user.id

    # Check if favorited
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == target_user_id,
            Favorite.deal_id == deal_id
        )
    )
    is_favorite = result.scalar_one_or_none() is not None

    return {"is_favorite": is_favorite}
