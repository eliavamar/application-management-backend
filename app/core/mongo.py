"""MongoDB connection and configuration."""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """MongoDB connection handler."""
    
    client: AsyncIOMotorClient | None = None
    database = None


mongodb = MongoDBConnection()


async def connect_to_mongodb() -> None:
    """Connect to MongoDB on startup."""
    try:
        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=settings.MONGODB_MAX_CONNECTIONS,
            minPoolSize=settings.MONGODB_MIN_CONNECTIONS,
        )
        mongodb.database = mongodb.client[settings.MONGODB_DATABASE]
        
        # Test connection
        await mongodb.client.admin.command('ping')
        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DATABASE}")
        
        # Create indexes
        await create_indexes()
        logger.info("MongoDB indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection() -> None:
    """Close MongoDB connection on shutdown."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Closed MongoDB connection")


async def create_indexes() -> None:
    """Create necessary indexes for performance."""
    try:
        # typed_items collection indexes
        typed_items = mongodb.database.typed_items
        
        # Index on type for fast filtering
        await typed_items.create_index([("type", 1)])
        
        # Index on owner_id for user-specific queries
        await typed_items.create_index([("owner_id", 1)])
        
        # Compound index for type + owner
        await typed_items.create_index([
            ("type", 1),
            ("owner_id", 1)
        ])
        
        # Text index for search functionality
        await typed_items.create_index([
            ("title", "text"),
            ("description", "text")
        ])
        
        # Index on created_at for sorting
        await typed_items.create_index([("created_at", -1)])
        
        # Index on tags for filtering
        await typed_items.create_index([("tags", 1)])
        
        # item_types collection indexes
        item_types = mongodb.database.item_types
        
        # Unique index on name
        await item_types.create_index([("name", 1)], unique=True)
        
        # Index on is_active
        await item_types.create_index([("is_active", 1)])
        
        # Index on created_by
        await item_types.create_index([("created_by", 1)])
        
    except Exception as e:
        logger.warning(f"Error creating indexes: {e}")


async def get_mongodb():
    """Dependency to get MongoDB database instance."""
    return mongodb.database
