from Yumeko.database import announcement_collection, DB_CACHE
from typing import Optional, Dict, Any, List
import asyncio

# Cache keys
ANNOUNCEMENT_CHAT_KEY = "announcement_chat_{}"
ANNOUNCEMENT_ENABLED_CHATS_KEY = "announcement_enabled_chats"

async def enable_announcements(chat_id: int, chat_title: str, chat_username: str = None, chat_link: str = None) -> None:
    """Enable announcements for a specific chat and save details."""
    try:
        # Prepare data
        chat_data = {
            "chat_id": chat_id,
            "announcements_enabled": True,
            "chat_title": chat_title,
            "chat_username": chat_username,
            "chat_link": chat_link,
        }
        
        # Update database
        await announcement_collection.update_one(
            {"chat_id": chat_id},
            {"$set": chat_data},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[ANNOUNCEMENT_CHAT_KEY.format(chat_id)] = chat_data
        
        # Invalidate enabled chats cache
        DB_CACHE.pop(ANNOUNCEMENT_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error enabling announcements: {e}")

async def disable_announcements(chat_id: int) -> None:
    """Disable announcements for a specific chat."""
    try:
        # Update database
        await announcement_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"announcements_enabled": False}},
            upsert=True
        )
        
        # Update cache
        cache_key = ANNOUNCEMENT_CHAT_KEY.format(chat_id)
        if cache_key in DB_CACHE:
            DB_CACHE[cache_key]["announcements_enabled"] = False
        
        # Invalidate enabled chats cache
        DB_CACHE.pop(ANNOUNCEMENT_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error disabling announcements: {e}")

async def is_announcements_enabled(chat_id: int) -> bool:
    """Check if announcements are enabled for a specific chat with caching."""
    try:
        # Get chat info with caching
        chat_data = await get_chat_info(chat_id)
        return chat_data.get("announcements_enabled", False) if chat_data else False
    except Exception as e:
        print(f"Error checking if announcements are enabled: {e}")
        return False

async def get_all_enabled_chats() -> List[Dict[str, Any]]:
    """Get all chats where announcements are enabled with caching."""
    try:
        # Check cache first
        if ANNOUNCEMENT_ENABLED_CHATS_KEY in DB_CACHE:
            return DB_CACHE[ANNOUNCEMENT_ENABLED_CHATS_KEY]
        
        # Get from database
        enabled_chats = await announcement_collection.find({"announcements_enabled": True}).to_list(length=None)
        
        # Update cache
        DB_CACHE[ANNOUNCEMENT_ENABLED_CHATS_KEY] = enabled_chats
        
        # Also update individual chat caches
        for chat in enabled_chats:
            DB_CACHE[ANNOUNCEMENT_CHAT_KEY.format(chat["chat_id"])] = chat
            
        return enabled_chats
    except Exception as e:
        print(f"Error getting enabled chats: {e}")
        return []

async def get_chat_info(chat_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve information about a specific chat with caching."""
    cache_key = ANNOUNCEMENT_CHAT_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        chat_data = await announcement_collection.find_one({"chat_id": chat_id})
        
        # Update cache
        if chat_data:
            DB_CACHE[cache_key] = chat_data
            
        return chat_data
    except Exception as e:
        print(f"Error getting chat info: {e}")
        return None