from Yumeko.database import chatbot_collection, DB_CACHE
from typing import Optional, Dict, Any, List
import asyncio

# Cache keys
CHATBOT_CHAT_KEY = "chatbot_chat_{}"
CHATBOT_ENABLED_CHATS_KEY = "chatbot_enabled_chats"

async def save_or_update_chat(chat_id: int, chat_username: str = None, chat_title: str = None, chat_link: str = None, chatbot_enabled: bool = False) -> None:
    """
    Save or update chat details in the database.
    If the chat exists, update its data. If not, create a new entry.
    """
    try:
        # Prepare data
        chat_data = {
            "chat_id": chat_id,
            "chat_username": chat_username,
            "chat_title": chat_title,
            "chat_link": chat_link,
            "chatbot_enabled": chatbot_enabled,
        }
        
        # Update database
        await chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": chat_data},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[CHATBOT_CHAT_KEY.format(chat_id)] = chat_data
        
        # Invalidate enabled chats cache if needed
        if chatbot_enabled:
            DB_CACHE.pop(CHATBOT_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error saving or updating chat: {e}")

async def enable_chatbot(chat_id: int, chat_title: str, chat_username: str = None, chat_link: str = None) -> None:
    """Enable chatbot for a specific chat and save details."""
    try:
        # Prepare data
        chat_data = {
            "chat_id": chat_id,
            "chatbot_enabled": True,
            "chat_title": chat_title,
            "chat_username": chat_username,
            "chat_link": chat_link,
        }
        
        # Update database
        await chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": chat_data},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[CHATBOT_CHAT_KEY.format(chat_id)] = chat_data
        
        # Invalidate enabled chats cache
        DB_CACHE.pop(CHATBOT_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error enabling chatbot: {e}")

async def disable_chatbot(chat_id: int) -> None:
    """Disable chatbot for a specific chat."""
    try:
        # Update database
        await chatbot_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"chatbot_enabled": False}},
            upsert=True
        )
        
        # Update cache
        cache_key = CHATBOT_CHAT_KEY.format(chat_id)
        if cache_key in DB_CACHE:
            DB_CACHE[cache_key]["chatbot_enabled"] = False
        
        # Invalidate enabled chats cache
        DB_CACHE.pop(CHATBOT_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error disabling chatbot: {e}")

async def is_chatbot_enabled(chat_id: int) -> bool:
    """Check if the chatbot is enabled for a specific chat with caching."""
    try:
        # Get chat info with caching
        chat_data = await get_chat_info(chat_id)
        return chat_data.get("chatbot_enabled", False) if chat_data else False
    except Exception as e:
        print(f"Error checking if chatbot is enabled: {e}")
        return False

async def get_all_enabled_chats() -> List[Dict[str, Any]]:
    """Get all chats where the chatbot is enabled with caching."""
    try:
        # Check cache first
        if CHATBOT_ENABLED_CHATS_KEY in DB_CACHE:
            return DB_CACHE[CHATBOT_ENABLED_CHATS_KEY]
        
        # Get from database
        enabled_chats = await chatbot_collection.find({"chatbot_enabled": True}).to_list(length=None)
        
        # Update cache
        DB_CACHE[CHATBOT_ENABLED_CHATS_KEY] = enabled_chats
        
        # Also update individual chat caches
        for chat in enabled_chats:
            DB_CACHE[CHATBOT_CHAT_KEY.format(chat["chat_id"])] = chat
            
        return enabled_chats
    except Exception as e:
        print(f"Error getting enabled chats: {e}")
        return []

async def get_chat_info(chat_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve information about a specific chat with caching."""
    cache_key = CHATBOT_CHAT_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        chat_data = await chatbot_collection.find_one({"chat_id": chat_id})
        
        # Update cache
        if chat_data:
            DB_CACHE[cache_key] = chat_data
            
        return chat_data
    except Exception as e:
        print(f"Error getting chat info: {e}")
        return None