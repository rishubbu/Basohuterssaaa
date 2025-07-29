from Yumeko.database import blacklist_collection, DB_CACHE
from typing import Optional, Dict, Any, List
import asyncio

# Cache keys
BLACKLIST_CHAT_KEY = "blacklist_chat_{}"
BLACKLIST_WORDS_KEY = "blacklist_words_chat_{}"
BLACKLIST_STICKERS_KEY = "blacklist_stickers_chat_{}"
BLACKLIST_MODE_KEY = "blacklist_mode_chat_{}"
BLACKLIST_STICKER_MODE_KEY = "blacklist_sticker_mode_chat_{}"
BLACKLIST_SUMMARY_KEY = "blacklist_summary"

# --- Word Blacklist Functions ---
async def add_blacklisted_word(chat_id: int, word: str) -> None:
    """Add a word to the blacklist for a specific chat."""
    try:
        # Update database
        await blacklist_collection.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"blacklisted_words": word}},
            upsert=True
        )
        
        # Invalidate cache
        DB_CACHE.pop(BLACKLIST_WORDS_KEY.format(chat_id), None)
        DB_CACHE.pop(BLACKLIST_CHAT_KEY.format(chat_id), None)
        DB_CACHE.pop(BLACKLIST_SUMMARY_KEY, None)
    except Exception as e:
        print(f"Error adding blacklisted word: {e}")

async def remove_blacklisted_word(chat_id: int, word: str) -> None:
    """Remove a word from the blacklist for a specific chat."""
    try:
        # Update database
        await blacklist_collection.update_one(
            {"chat_id": chat_id},
            {"$pull": {"blacklisted_words": word}},
        )
        
        # Invalidate cache
        DB_CACHE.pop(BLACKLIST_WORDS_KEY.format(chat_id), None)
        DB_CACHE.pop(BLACKLIST_CHAT_KEY.format(chat_id), None)
        DB_CACHE.pop(BLACKLIST_SUMMARY_KEY, None)
    except Exception as e:
        print(f"Error removing blacklisted word: {e}")

async def get_blacklisted_words(chat_id: int) -> List[str]:
    """Retrieve the list of blacklisted words for a specific chat with caching."""
    cache_key = BLACKLIST_WORDS_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        chat_data = await blacklist_collection.find_one({"chat_id": chat_id})
        words = chat_data.get("blacklisted_words", []) if chat_data else []
        
        # Update cache
        DB_CACHE[cache_key] = words
        
        return words
    except Exception as e:
        print(f"Error getting blacklisted words: {e}")
        return []

async def set_blacklist_mode(chat_id: int, mode: str, duration: int = 0) -> None:
    """
    Set the blacklist mode for a specific chat.
    Mode can be: off, del, ban, kick, mute, tban, tmute.
    Duration is only relevant for tban or tmute.
    """
    try:
        # Prepare mode data
        mode_data = {"mode": mode}
        if mode in ["tban", "tmute"]:
            mode_data["duration"] = duration
            
        # Update database
        await blacklist_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"blacklist_mode": mode_data}},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[BLACKLIST_MODE_KEY.format(chat_id)] = mode_data
        DB_CACHE.pop(BLACKLIST_CHAT_KEY.format(chat_id), None)
    except Exception as e:
        print(f"Error setting blacklist mode: {e}")

async def get_blacklist_mode(chat_id: int) -> Dict[str, Any]:
    """Retrieve the blacklist mode for a specific chat with caching."""
    cache_key = BLACKLIST_MODE_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        chat_data = await blacklist_collection.find_one({"chat_id": chat_id})
        mode_data = chat_data.get("blacklist_mode", {"mode": "off"}) if chat_data else {"mode": "off"}
        
        # Update cache
        DB_CACHE[cache_key] = mode_data
        
        return mode_data
    except Exception as e:
        print(f"Error getting blacklist mode: {e}")
        return {"mode": "off"}

# --- Sticker Blacklist Functions ---
async def add_blacklisted_sticker(chat_id: int, sticker_id: str) -> None:
    """Add a sticker to the blacklist for a specific chat."""
    try:
        # Update database
        await blacklist_collection.update_one(
            {"chat_id": chat_id},
            {"$addToSet": {"blacklisted_stickers": sticker_id}},
            upsert=True
        )
        
        # Invalidate cache
        DB_CACHE.pop(BLACKLIST_STICKERS_KEY.format(chat_id), None)
        DB_CACHE.pop(BLACKLIST_CHAT_KEY.format(chat_id), None)
        DB_CACHE.pop(BLACKLIST_SUMMARY_KEY, None)
    except Exception as e:
        print(f"Error adding blacklisted sticker: {e}")

async def remove_blacklisted_sticker(chat_id: int, sticker_id: str) -> None:
    """Remove a sticker from the blacklist for a specific chat."""
    try:
        # Update database
        await blacklist_collection.update_one(
            {"chat_id": chat_id},
            {"$pull": {"blacklisted_stickers": sticker_id}},
        )
        
        # Invalidate cache
        DB_CACHE.pop(BLACKLIST_STICKERS_KEY.format(chat_id), None)
        DB_CACHE.pop(BLACKLIST_CHAT_KEY.format(chat_id), None)
        DB_CACHE.pop(BLACKLIST_SUMMARY_KEY, None)
    except Exception as e:
        print(f"Error removing blacklisted sticker: {e}")

async def get_blacklisted_stickers(chat_id: int) -> List[str]:
    """Retrieve the list of blacklisted stickers for a specific chat with caching."""
    cache_key = BLACKLIST_STICKERS_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        chat_data = await blacklist_collection.find_one({"chat_id": chat_id})
        stickers = chat_data.get("blacklisted_stickers", []) if chat_data else []
        
        # Update cache
        DB_CACHE[cache_key] = stickers
        
        return stickers
    except Exception as e:
        print(f"Error getting blacklisted stickers: {e}")
        return []

async def set_blacklist_sticker_mode(chat_id: int, mode: str, duration: int = 0) -> None:
    """
    Set the blacklist sticker mode for a specific chat.
    Mode can be: delete, ban, mute, tban, tmute.
    Duration is only relevant for tban or tmute.
    """
    try:
        # Prepare mode data
        mode_data = {"mode": mode}
        if mode in ["tban", "tmute"]:
            mode_data["duration"] = duration
            
        # Update database
        await blacklist_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"sticker_mode": mode_data}},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[BLACKLIST_STICKER_MODE_KEY.format(chat_id)] = mode_data
        DB_CACHE.pop(BLACKLIST_CHAT_KEY.format(chat_id), None)
    except Exception as e:
        print(f"Error setting blacklist sticker mode: {e}")

async def get_blacklist_sticker_mode(chat_id: int) -> Dict[str, Any]:
    """Retrieve the blacklist sticker mode for a specific chat with caching."""
    cache_key = BLACKLIST_STICKER_MODE_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        chat_data = await blacklist_collection.find_one({"chat_id": chat_id})
        mode_data = chat_data.get("sticker_mode", {"mode": "delete"}) if chat_data else {"mode": "delete"}
        
        # Update cache
        DB_CACHE[cache_key] = mode_data
        
        return mode_data
    except Exception as e:
        print(f"Error getting blacklist sticker mode: {e}")
        return {"mode": "delete"}

async def get_blacklist_summary() -> Dict[str, int]:
    """
    Calculate the total number of blacklisted words and stickers across all chats
    and the number of chats with blacklisted words or stickers with caching.
    
    Returns:
        dict: A dictionary containing the counts.
            {
                "total_blacklisted_words": int,
                "total_blacklisted_stickers": int,
                "chats_with_blacklisted_words": int,
                "chats_with_blacklisted_stickers": int
            }
    """
    # Check cache first
    if BLACKLIST_SUMMARY_KEY in DB_CACHE:
        return DB_CACHE[BLACKLIST_SUMMARY_KEY]
    
    try:
        cursor = blacklist_collection.find({})
        total_blacklisted_words = 0
        total_blacklisted_stickers = 0
        chats_with_blacklisted_words = 0
        chats_with_blacklisted_stickers = 0

        async for chat_data in cursor:
            # Count blacklisted words
            blacklisted_words = chat_data.get("blacklisted_words", [])
            if blacklisted_words:
                total_blacklisted_words += len(blacklisted_words)
                chats_with_blacklisted_words += 1

            # Count blacklisted stickers
            blacklisted_stickers = chat_data.get("blacklisted_stickers", [])
            if blacklisted_stickers:
                total_blacklisted_stickers += len(blacklisted_stickers)
                chats_with_blacklisted_stickers += 1

        summary = {
            "total_blacklisted_words": total_blacklisted_words,
            "total_blacklisted_stickers": total_blacklisted_stickers,
            "chats_with_blacklisted_words": chats_with_blacklisted_words,
            "chats_with_blacklisted_stickers": chats_with_blacklisted_stickers
        }
        
        # Update cache
        DB_CACHE[BLACKLIST_SUMMARY_KEY] = summary
        
        return summary
    except Exception as e:
        print(f"Error getting blacklist summary: {e}")
        return {
            "total_blacklisted_words": 0,
            "total_blacklisted_stickers": 0,
            "chats_with_blacklisted_words": 0,
            "chats_with_blacklisted_stickers": 0
        }
