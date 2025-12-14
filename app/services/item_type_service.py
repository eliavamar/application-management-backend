"""Service layer for item type management."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.core.mongo import mongodb
from app.models_mongo import ItemType, ItemTypeCreate, ItemTypeUpdate, ItemTypesPublic


class ItemTypeService:
    """Service for managing item types."""
    
    @property
    def collection(self):
        """Get the item_types collection."""
        return mongodb.database.item_types
    
    async def list_types(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> ItemTypesPublic:
        """List all item types."""
        query = {"is_active": True} if active_only else {}
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        types = await cursor.to_list(length=limit)
        count = await self.collection.count_documents(query)
        
        return ItemTypesPublic(
            data=[ItemType(**t) for t in types],
            count=count
        )
    
    async def get_type_by_id(self, type_id: str) -> Optional[ItemType]:
        """Get item type by ID."""
        doc = await self.collection.find_one({"_id": type_id})
        return ItemType(**doc) if doc else None
    
    async def get_type_by_name(self, name: str) -> Optional[ItemType]:
        """Get item type by name."""
        doc = await self.collection.find_one({"name": name.lower()})
        return ItemType(**doc) if doc else None
    
    async def create_type(
        self,
        type_in: ItemTypeCreate,
        created_by: UUID
    ) -> ItemType:
        """Create new item type."""
        type_data = type_in.model_dump()
        type_data["name"] = type_data["name"].lower()
        type_data["created_by"] = created_by
        type_data["created_at"] = datetime.utcnow()
        type_data["updated_at"] = datetime.utcnow()
        
        from uuid import uuid4
        type_id = str(uuid4())
        type_data["_id"] = type_id
        
        await self.collection.insert_one(type_data)
        
        return ItemType(**type_data)
    
    async def update_type(
        self,
        type_id: str,
        type_in: ItemTypeUpdate
    ) -> ItemType:
        """Update item type."""
        update_data = type_in.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        if "name" in update_data:
            update_data["name"] = update_data["name"].lower()
        
        await self.collection.update_one(
            {"_id": type_id},
            {"$set": update_data}
        )
        
        doc = await self.collection.find_one({"_id": type_id})
        return ItemType(**doc)
    
    async def delete_type(self, type_id: str) -> bool:
        """Delete item type."""
        result = await self.collection.delete_one({"_id": type_id})
        return result.deleted_count > 0
