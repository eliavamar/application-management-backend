"""MongoDB data models for typed items."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class FieldType(str, Enum):
    """Supported field types for item attributes."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    ENUM = "enum"
    URL = "url"
    EMAIL = "email"


class FieldDefinition(BaseModel):
    """Definition of a custom field in an item type."""
    name: str = Field(..., description="Field name (snake_case)")
    label: str = Field(..., description="Display label")
    field_type: FieldType = Field(..., description="Data type")
    required: bool = Field(default=False, description="Is field required")
    default_value: Any = Field(default=None, description="Default value")
    options: Optional[List[str]] = Field(default=None, description="Options for enum type")
    min_value: Optional[float] = Field(default=None, description="Min value for numbers")
    max_value: Optional[float] = Field(default=None, description="Max value for numbers")
    min_length: Optional[int] = Field(default=None, description="Min length for strings")
    max_length: Optional[int] = Field(default=None, description="Max length for strings")
    pattern: Optional[str] = Field(default=None, description="Regex pattern for validation")
    help_text: Optional[str] = Field(default=None, description="Help text for users")


class ItemTypeBase(BaseModel):
    """Base model for item types."""
    name: str = Field(..., min_length=1, max_length=50, description="Type name (singular)")
    plural_name: str = Field(..., min_length=1, max_length=50, description="Plural name")
    description: Optional[str] = Field(default=None, max_length=500)
    icon: Optional[str] = Field(default=None, description="Icon name or emoji")
    color: Optional[str] = Field(default=None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color")
    fields: List[FieldDefinition] = Field(default_factory=list, description="Custom fields")
    is_active: bool = Field(default=True, description="Is type active")


class ItemTypeCreate(ItemTypeBase):
    """Model for creating item types."""
    pass


class ItemTypeUpdate(BaseModel):
    """Model for updating item types."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    plural_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    icon: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern=r'^#[0-9A-Fa-f]{6}$')
    fields: Optional[List[FieldDefinition]] = None
    is_active: Optional[bool] = None


class ItemType(ItemTypeBase):
    """Complete item type model with MongoDB fields."""
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: UUID = Field(..., description="User who created this type")
    
    model_config = {"populate_by_name": True}


class ItemTypesPublic(BaseModel):
    """Response model for listing item types."""
    data: List[ItemType]
    count: int


# Typed Items Models
class TypedItemBase(BaseModel):
    """Base model for typed items."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    type: str = Field(..., description="Item type name")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Type-specific attributes")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    is_public: bool = Field(default=False, description="Is item publicly visible")


class TypedItemCreate(TypedItemBase):
    """Model for creating typed items."""
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that type exists (checked in service layer)."""
        return v.lower().strip()


class TypedItemUpdate(BaseModel):
    """Model for updating typed items."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    attributes: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class TypedItem(TypedItemBase):
    """Complete typed item model with MongoDB fields."""
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    owner_id: UUID = Field(..., description="Owner user ID (from PostgreSQL)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"populate_by_name": True}


class TypedItemPublic(TypedItemBase):
    """Public model for typed items."""
    id: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class TypedItemsPublic(BaseModel):
    """Response model for listing typed items."""
    data: List[TypedItemPublic]
    count: int
    types: Dict[str, int] = Field(default_factory=dict, description="Count by type")


class TypedItemStats(BaseModel):
    """Statistics for typed items."""
    total_items: int
    items_by_type: Dict[str, int]
    recent_items: List[TypedItemPublic]
    popular_tags: List[Dict[str, Any]]
