"""Service layer for typed item management."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from app.core.mongo import mongodb
from app.models_mongo import (
    TypedItem,
    TypedItemCreate,
    TypedItemUpdate,
    TypedItemsPublic,
    TypedItemStats,
    ItemType,
    FieldType
)


class TypedItemService:
    """Service for managing typed items."""
    
    @property
    def collection(self):
        """Get the typed_items collection."""
        return mongodb.database.typed_items
    
    async def list_items(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> TypedItemsPublic:
        """List typed items with filters."""
        query = filters or {}
        
        # Add text search if provided
        if search:
            query["$text"] = {"$search": search}
        
        # Get items
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        items = await cursor.to_list(length=limit)
        
        # Get total count
        count = await self.collection.count_documents(query)
        
        # Get counts by type
        pipeline = [
            {"$match": filters or {}},
            {"$group": {"_id": "$type", "count": {"$sum": 1}}}
        ]
        type_counts = await self.collection.aggregate(pipeline).to_list(None)
        types_dict = {item["_id"]: item["count"] for item in type_counts}
        
        return TypedItemsPublic(
            data=[TypedItem(**item) for item in items],
            count=count,
            types=types_dict
        )
    
    async def get_item_by_id(self, item_id: str) -> Optional[TypedItem]:
        """Get typed item by ID."""
        doc = await self.collection.find_one({"_id": item_id})
        return TypedItem(**doc) if doc else None
    
    async def create_item(
        self,
        item_in: TypedItemCreate,
        owner_id: UUID
    ) -> TypedItem:
        """Create new typed item."""
        item_data = item_in.model_dump()
        item_data["type"] = item_data["type"].lower()
        item_data["owner_id"] = owner_id
        item_data["created_at"] = datetime.utcnow()
        item_data["updated_at"] = datetime.utcnow()
        
        item_id = str(uuid4())
        item_data["_id"] = item_id
        
        await self.collection.insert_one(item_data)
        
        return TypedItem(**item_data)
    
    async def update_item(
        self,
        item_id: str,
        item_in: TypedItemUpdate
    ) -> TypedItem:
        """Update typed item."""
        update_data = item_in.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await self.collection.update_one(
            {"_id": item_id},
            {"$set": update_data}
        )
        
        doc = await self.collection.find_one({"_id": item_id})
        return TypedItem(**doc)
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete typed item."""
        result = await self.collection.delete_one({"_id": item_id})
        return result.deleted_count > 0
    
    async def count_by_type_id(self, type_id: str) -> int:
        """Count items of specific type."""
        return await self.collection.count_documents({"type": type_id})
    
    async def get_stats(self, owner_id: Optional[UUID] = None) -> TypedItemStats:
        """Get statistics for typed items."""
        query = {"owner_id": owner_id} if owner_id else {}
        
        # Total count
        total = await self.collection.count_documents(query)
        
        # Count by type
        pipeline = [
            {"$match": query},
            {"$group": {"_id": "$type", "count": {"$sum": 1}}}
        ]
        type_counts = await self.collection.aggregate(pipeline).to_list(None)
        by_type = {item["_id"]: item["count"] for item in type_counts}
        
        # Recent items
        cursor = self.collection.find(query).sort("created_at", -1).limit(5)
        recent = await cursor.to_list(length=5)
        
        # Popular tags
        pipeline = [
            {"$match": query},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        tag_counts = await self.collection.aggregate(pipeline).to_list(None)
        popular_tags = [{"tag": item["_id"], "count": item["count"]} for item in tag_counts]
        
        return TypedItemStats(
            total_items=total,
            items_by_type=by_type,
            recent_items=[TypedItem(**item) for item in recent],
            popular_tags=popular_tags
        )
    
    async def search_items(
        self,
        query: str,
        owner_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> TypedItemsPublic:
        """Search items by text."""
        search_query = {"$text": {"$search": query}}
        if owner_id:
            search_query["owner_id"] = owner_id
        
        return await self.list_items(
            filters=search_query,
            skip=skip,
            limit=limit
        )
    
    async def validate_attributes(
        self,
        attributes: Dict[str, Any],
        item_type: ItemType
    ) -> List[Dict[str, str]]:
        """Validate attributes against item type schema."""
        errors = []
        
        # Create field map
        field_map = {field.name: field for field in item_type.fields}
        
        # Check required fields
        for field_def in item_type.fields:
            if field_def.required and field_def.name not in attributes:
                errors.append({
                    "field": field_def.name,
                    "message": f"{field_def.label} is required"
                })
        
        # Validate each attribute
        for field_name, value in attributes.items():
            if field_name not in field_map:
                errors.append({
                    "field": field_name,
                    "message": f"Unknown field '{field_name}' for type '{item_type.name}'"
                })
                continue
            
            field_def = field_map[field_name]
            
            # Type validation
            if value is not None:
                field_errors = self._validate_field_value(value, field_def)
                errors.extend(field_errors)
        
        return errors
    
    def _validate_field_value(
        self,
        value: Any,
        field_def
    ) -> List[Dict[str, str]]:
        """Validate a single field value."""
        errors = []
        field_name = field_def.name
        
        try:
            if field_def.field_type == FieldType.STRING:
                if not isinstance(value, str):
                    errors.append({
                        "field": field_name,
                        "message": f"{field_def.label} must be a string"
                    })
                elif field_def.min_length and len(value) < field_def.min_length:
                    errors.append({
                        "field": field_name,
                        "message": f"{field_def.label} must be at least {field_def.min_length} characters"
                    })
                elif field_def.max_length and len(value) > field_def.max_length:
                    errors.append({
                        "field": field_name,
                        "message": f"{field_def.label} must be at most {field_def.max_length} characters"
                    })
                
            elif field_def.field_type == FieldType.NUMBER:
                if not isinstance(value, (int, float)):
                    errors.append({
                        "field": field_name,
                        "message": f"{field_def.label} must be a number"
                    })
                elif field_def.min_value is not None and value < field_def.min_value:
                    errors.append({
                        "field": field_name,
                        "message": f"{field_def.label} must be at least {field_def.min_value}"
                    })
                elif field_def.max_value is not None and value > field_def.max_value:
                    errors.append({
                        "field": field_name,
                        "message": f"{field_def.label} must be at most {field_def.max_value}"
                    })
            
            elif field_def.field_type == FieldType.BOOLEAN:
                if not isinstance(value, bool):
                    errors.append({
                        "field": field_name,
                        "message": f"{field_def.label} must be true or false"
                    })
            
            elif field_def.field_type == FieldType.ENUM:
                if value not in (field_def.options or []):
                    errors.append({
                        "field": field_name,
                        "message": f"{field_def.label} must be one of: {', '.join(field_def.options or [])}"
                    })
        
        except Exception as e:
            errors.append({
                "field": field_name,
                "message": f"Validation error: {str(e)}"
            })
        
        return errors
