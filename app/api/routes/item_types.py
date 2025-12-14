"""API routes for item type management."""
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import CurrentUser, get_current_active_superuser
from app.models_mongo import (
    ItemType,
    ItemTypeCreate,
    ItemTypeUpdate,
    ItemTypesPublic
)
from app.services.item_type_service import ItemTypeService

router = APIRouter(prefix="/item-types", tags=["item-types"])


@router.get("/", response_model=ItemTypesPublic)
async def list_item_types(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> Any:
    """List all item types."""
    service = ItemTypeService()
    result = await service.list_types(
        skip=skip,
        limit=limit,
        active_only=active_only
    )
    return result


@router.get("/{id}", response_model=ItemType)
async def get_item_type(
    id: str,
    current_user: CurrentUser
) -> Any:
    """Get item type by ID."""
    service = ItemTypeService()
    item_type = await service.get_type_by_id(id)
    if not item_type:
        raise HTTPException(status_code=404, detail="Item type not found")
    return item_type


@router.post("/", response_model=ItemType)
async def create_item_type(
    item_type_in: ItemTypeCreate,
    current_user: CurrentUser = Depends(get_current_active_superuser)
) -> Any:
    """Create new item type (admin only)."""
    service = ItemTypeService()
    
    # Check if type already exists
    existing = await service.get_type_by_name(item_type_in.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Item type '{item_type_in.name}' already exists"
        )
    
    item_type = await service.create_type(item_type_in, current_user.id)
    return item_type


@router.put("/{id}", response_model=ItemType)
async def update_item_type(
    id: str,
    item_type_in: ItemTypeUpdate,
    current_user: CurrentUser = Depends(get_current_active_superuser)
) -> Any:
    """Update item type (admin only)."""
    service = ItemTypeService()
    
    existing = await service.get_type_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item type not found")
    
    updated = await service.update_type(id, item_type_in)
    return updated


@router.delete("/{id}")
async def delete_item_type(
    id: str,
    current_user: CurrentUser = Depends(get_current_active_superuser)
) -> Any:
    """Delete item type (admin only)."""
    service = ItemTypeService()
    
    # Check if type has items
    from app.services.typed_item_service import TypedItemService
    item_service = TypedItemService()
    count = await item_service.count_by_type_id(id)
    
    if count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete type with {count} existing items"
        )
    
    success = await service.delete_type(id)
    if not success:
        raise HTTPException(status_code=404, detail="Item type not found")
    
    return {"message": "Item type deleted successfully"}
