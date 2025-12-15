from typing import Any

from fastapi import APIRouter
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message, DashboardStats

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get dashboard statistics.
    """
    # Get total items count
    total_count_statement = select(func.count()).select_from(Item)
    total_items = session.exec(total_count_statement).one()
    
    # Get user's items count
    user_count_statement = (
        select(func.count())
        .select_from(Item)
        .where(Item.owner_id == current_user.id)
    )
    user_items = session.exec(user_count_statement).one()
    
    # Get recent items (last 5)
    recent_statement = (
        select(Item)
        .order_by(Item.created_at.desc())
        .limit(5)
    )
    recent_items = session.exec(recent_statement).all()
    
    return DashboardStats(
        total_items=total_items,
        user_items=user_items,
        recent_items=recent_items
    )


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items.
    """
    count_statement = select(func.count()).select_from(Item).where(Item.owner_id == current_user.id)
    count = session.exec(count_statement).one()
    statement = (
        select(Item)
        .where(Item.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return ItemsPublic(data=items, count=count)


@router.post("/", response_model=ItemPublic)
def create_item(
    session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
    db_item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: str) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise Exception("Item not found")
    if item.owner_id != current_user.id and not current_user.is_superuser:
        raise Exception("Not enough permissions")
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    session: SessionDep, current_user: CurrentUser, id: str, item_in: ItemUpdate
) -> Any:
    """
    Update an item.
    """
    item = session.get(Item, id)
    if not item:
        raise Exception("Item not found")
    if item.owner_id != current_user.id and not current_user.is_superuser:
        raise Exception("Not enough permissions")
    update_data = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_item(session: SessionDep, current_user: CurrentUser, id: str) -> Message:
    """
    Delete an item.
    """
    item = session.get(Item, id)
    if not item:
        raise Exception("Item not found")
    if item.owner_id != current_user.id and not current_user.is_superuser:
        raise Exception("Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
