from Yumeko.database import afk_collection, DB_CACHE
from typing import Optional, Dict, Any

# Cache keys
AFK_USER_KEY = "afk_user_{}"
AFK_USERNAME_KEY = "afk_username_{}"

async def set_afk(user_id: int, user_first_name: str, username: str, afk_reason: str, afk_start_time: str, media_id: str = None) -> None:
    """Set AFK details for a specific user."""
    try:
        # Prepare data
        afk_data = {
            "user_id": user_id,
            "user_first_name": user_first_name,
            "username": username,
            "afk_reason": afk_reason,
            "afk_start_time": afk_start_time,
            "media_id": media_id
        }
        
        # Update database
        await afk_collection.update_one(
            {"user_id": user_id},
            {"$set": afk_data},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[AFK_USER_KEY.format(user_id)] = afk_data
        if username:
            DB_CACHE[AFK_USERNAME_KEY.format(username)] = afk_data
    except Exception as e:
        # Log error but don't crash
        print(f"Error setting AFK status: {e}")

async def get_afk(user_id: int) -> Optional[Dict[str, Any]]:
    """Get the AFK details for a specific user with caching."""
    cache_key = AFK_USER_KEY.format(user_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        user_data = await afk_collection.find_one({"user_id": user_id})
        
        # Update cache
        if user_data:
            DB_CACHE[cache_key] = user_data
            
        return user_data
    except Exception as e:
        print(f"Error getting AFK status: {e}")
        return None

async def clear_afk(user_id: int) -> None:
    """Clear AFK details for a specific user."""
    try:
        # Get user data first to clear username cache if needed
        user_data = await get_afk(user_id)
        
        # Delete from database
        await afk_collection.delete_one({"user_id": user_id})
        
        # Clear caches
        DB_CACHE.pop(AFK_USER_KEY.format(user_id), None)
        if user_data and user_data.get("username"):
            DB_CACHE.pop(AFK_USERNAME_KEY.format(user_data["username"]), None)
    except Exception as e:
        print(f"Error clearing AFK status: {e}")

async def get_afk_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get the AFK details for a specific user by username with caching."""
    if not username:
        return None
        
    cache_key = AFK_USERNAME_KEY.format(username)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        user_data = await afk_collection.find_one({"username": username})
        
        # Process and cache result
        if user_data:
            result = {
                "user_id": user_data["user_id"],
                "user_first_name": user_data["user_first_name"],
                "afk_start_time": user_data["afk_start_time"],
                "afk_reason": user_data.get("afk_reason"),
                "media_id": user_data.get("media_id"),
            }
            DB_CACHE[cache_key] = result
            return result
        return None
    except Exception as e:
        print(f"Error getting AFK status by username: {e}")
        return None

async def is_user_afk(user_id: int) -> bool:
    """Check if a user is currently AFK with caching."""
    try:
        user_data = await get_afk(user_id)
        return bool(user_data)
    except Exception as e:
        print(f"Error checking if user is AFK: {e}")
        return False
