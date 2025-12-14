"""API routes for typed item management."""
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from app.api.deps import CurrentUser
from app.models_mongo import (
    TypedItem,
    TypedItemCreate,
    TypedItemUpdate,
    TypedItemsPublic,
    TypedItemStats
)
from app.services.typed_item_service import TypedItemService
from app.services.item_type_service import ItemTypeService

router = APIRouter(prefix="/typed-items", tags=["typed-items"])


@router.get("/", response_model=TypedItemsPublic)
async def list_typed_items(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = None
) -> Any:
    """List typed items with optional filters."""
    service = TypedItemService()
    
    # Parse tags
    tag_list = tags.split(",") if tags else None
    
    # Build filter
    filters = {}
    if type:
        filters["type"] = type.lower()
    if tag_list:
        filters["tags"] = {"$in": tag_list}
    
    # Add user filter
    if not current_user.is_superuser:
        filters["owner_id"] = current_user.id
    
    result = await service.list_items(
        filters=filters,
        skip=skip,
        limit=limit,
        search=search
    )
    return result


@router.get("/stats", response_model=TypedItemStats)
async def get_typed_items_stats(
    current_user: CurrentUser
) -> Any:
    """Get statistics for typed items."""
    service = TypedItemService()
    
    # Filter by user if not admin
    owner_id = None if current_user.is_superuser else current_user.id
    
    stats = await service.get_stats(owner_id=owner_id)
    return stats


@router.get("/by-type/{type}", response_model=TypedItemsPublic)
async def list_items_by_type(
    type: str,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """List items by specific type."""
    service = TypedItemService()
    
    # Verify type exists
    type_service = ItemTypeService()
    item_type = await type_service.get_type_by_name(type)
    if not item_type:
        raise HTTPException(status_code=404, detail=f"Item type '{type}' not found")
    
    # Build filter
    filters = {"type": type.lower()}
    if not current_user.is_superuser:
        filters["owner_id"] = current_user.id
    
    result = await service.list_items(
        filters=filters,
        skip=skip,
        limit=limit
    )
    return result


@router.get("/{id}", response_model=TypedItem)
async def get_typed_item(
    id: str,
    current_user: CurrentUser
) -> Any:
    """Get typed item by ID."""
    service = TypedItemService()
    item = await service.get_item_by_id(id)
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check permissions
    if not current_user.is_superuser and item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return item


@router.post("/", response_model=TypedItem)
async def create_typed_item(
    item_in: TypedItemCreate,
    current_user: CurrentUser
) -> Any:
    """Create new typed item."""
    # Verify type exists
    type_service = ItemTypeService()
    item_type = await type_service.get_type_by_name(item_in.type)
    if not item_type:
        raise HTTPException(
            status_code=404,
            detail=f"Item type '{item_in.type}' not found"
        )
    
    if not item_type.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"Item type '{item_in.type}' is not active"
        )
    
    # Validate attributes against type schema
    service = TypedItemService()
    validation_errors = await service.validate_attributes(
        item_in.attributes,
        item_type
    )
    if validation_errors:
        raise HTTPException(
            status_code=400,
            detail={"message": "Validation failed", "errors": validation_errors}
        )
    
    # Create item
    item = await service.create_item(item_in, current_user.id)
    return item


@router.put("/{id}", response_model=TypedItem)
async def update_typed_item(
    id: str,
    item_in: TypedItemUpdate,
    current_user: CurrentUser
) -> Any:
    """Update typed item."""
    service = TypedItemService()
    
    # Get existing item
    existing = await service.get_item_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check permissions
    if not current_user.is_superuser and existing.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Validate attributes if provided
    if item_in.attributes is not None:
        type_service = ItemTypeService()
        item_type = await type_service.get_type_by_name(existing.type)
        
        validation_errors = await service.validate_attributes(
            item_in.attributes,
            item_type
        )
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail={"message": "Validation failed", "errors": validation_errors}
            )
    
    # Update item
    updated = await service.update_item(id, item_in)
    return updated


@router.delete("/{id}")
async def delete_typed_item(
    id: str,
    current_user: CurrentUser
) -> Any:
    """Delete typed item."""
    service = TypedItemService()
    
    # Get existing item
    existing = await service.get_item_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check permissions
    if not current_user.is_superuser and existing.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Delete item
    success = await service.delete_item(id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted successfully"}


@router.post("/search", response_model=TypedItemsPublic)
async def search_typed_items(
    query: str,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """Advanced text search across typed items."""
    service = TypedItemService()
    
    # Add user filter
    owner_id = None if current_user.is_superuser else current_user.id
    
    result = await service.search_items(
        query=query,
        owner_id=owner_id,
        skip=skip,
        limit=limit
    )
    return result
