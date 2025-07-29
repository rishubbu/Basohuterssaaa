from Yumeko.database import nightmode_collection, DB_CACHE
from typing import Optional, Dict, Any, List
import asyncio

# Cache keys
NIGHTMODE_CHAT_KEY = "nightmode_chat_{}"
NIGHTMODE_ENABLED_CHATS_KEY = "nightmode_enabled_chats"

async def enable_nightmode(chat_id: int, chat_title: str, chat_username: str = None, chat_link: str = None) -> None:
    """Enable night mode for a specific chat and save details with caching."""
    try:
        # Prepare data
        chat_data = {
            "chat_id": chat_id,
            "nightmode_enabled": True,
            "chat_title": chat_title,
            "chat_username": chat_username,
            "chat_link": chat_link,
        }
        
        # Update database
        await nightmode_collection.update_one(
            {"chat_id": chat_id},
            {"$set": chat_data},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[NIGHTMODE_CHAT_KEY.format(chat_id)] = chat_data
        
        # Invalidate enabled chats cache
        DB_CACHE.pop(NIGHTMODE_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error enabling nightmode: {e}")

async def disable_nightmode(chat_id: int) -> None:
    """Disable night mode for a specific chat with cache invalidation."""
    try:
        # Update database
        await nightmode_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"nightmode_enabled": False}},
            upsert=True
        )
        
        # Update cache
        cache_key = NIGHTMODE_CHAT_KEY.format(chat_id)
        if cache_key in DB_CACHE:
            DB_CACHE[cache_key]["nightmode_enabled"] = False
        
        # Invalidate enabled chats cache
        DB_CACHE.pop(NIGHTMODE_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error disabling nightmode: {e}")

async def is_nightmode_enabled(chat_id: int) -> bool:
    """Check if night mode is enabled for a specific chat with caching."""
    try:
        # Get chat info with caching
        chat_data = await get_nightmode_chat_info(chat_id)
        return chat_data.get("nightmode_enabled", False) if chat_data else False
    except Exception as e:
        print(f"Error checking if nightmode is enabled: {e}")
        return False

async def get_nightmode_chat_info(chat_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve information about a specific chat in night mode with caching."""
    cache_key = NIGHTMODE_CHAT_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        chat_data = await nightmode_collection.find_one({"chat_id": chat_id})
        
        # Update cache
        if chat_data:
            DB_CACHE[cache_key] = chat_data
            
        return chat_data
    except Exception as e:
        print(f"Error getting nightmode chat info: {e}")
        return None

async def get_all_nightmode_enabled_chats() -> List[int]:
    """Retrieve all chat IDs with night mode enabled with caching."""
    # Check cache first
    if NIGHTMODE_ENABLED_CHATS_KEY in DB_CACHE:
        return DB_CACHE[NIGHTMODE_ENABLED_CHATS_KEY]
    
    try:
        # Get from database
        cursor = nightmode_collection.find({"nightmode_enabled": True}, {"chat_id": 1, "_id": 0})
        chat_ids = [chat["chat_id"] async for chat in cursor]
        
        # Update cache
        DB_CACHE[NIGHTMODE_ENABLED_CHATS_KEY] = chat_ids
        
        return chat_ids
    except Exception as e:
        print(f"Error getting all nightmode enabled chats: {e}")
        return []
