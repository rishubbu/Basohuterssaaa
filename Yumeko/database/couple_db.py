from Yumeko.database import couple_collection, waifu_collection, DB_CACHE
from datetime import datetime
from pytz import timezone
from typing import Optional, Dict, Any, List

# Define IST timezone
IST = timezone('Asia/Kolkata')

# Cache keys
COUPLE_CHAT_KEY = "couple_chat_{}"
COUPLE_ALL_KEY = "couple_all"
WAIFU_USER_KEY = "waifu_user_{}"

async def save_couple(chat_id: int, couple_id: int, couple_first_name: str, couple_id_2: int, couple_first_name_2: str) -> None:
    """Save the couple details in the database with caching."""
    try:
        # Get current date in IST
        date_chosen = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare data
        data = {
            "chat_id": chat_id,
            "couple_id": couple_id,
            "couple_first_name": couple_first_name,
            "couple_id_2": couple_id_2,
            "couple_first_name_2": couple_first_name_2,
            "date": date_chosen
        }
        
        # Update database
        await couple_collection.update_one(
            {"chat_id": chat_id},
            {"$set": data},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[COUPLE_CHAT_KEY.format(chat_id)] = data
        
        # Invalidate all couples cache
        DB_CACHE.pop(COUPLE_ALL_KEY, None)
    except Exception as e:
        print(f"Error saving couple: {e}")

async def is_couple_already_chosen(chat_id: int) -> bool:
    """Check if a couple is already chosen for the given chat with caching."""
    try:
        # Get couple with caching
        couple = await get_couple(chat_id)
        return couple is not None
    except Exception as e:
        print(f"Error checking if couple is already chosen: {e}")
        return False

async def get_couple(chat_id: int) -> Optional[Dict[str, Any]]:
    """Get the couple details for the given chat with caching."""
    cache_key = COUPLE_CHAT_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        couple = await couple_collection.find_one({"chat_id": chat_id})
        
        # Update cache
        if couple:
            DB_CACHE[cache_key] = couple
            
        return couple
    except Exception as e:
        print(f"Error getting couple: {e}")
        return None

async def remove_couple(chat_id: int) -> None:
    """Remove the couple details from the database with cache invalidation."""
    try:
        # Delete from database
        await couple_collection.delete_one({"chat_id": chat_id})
        
        # Invalidate caches
        DB_CACHE.pop(COUPLE_CHAT_KEY.format(chat_id), None)
        DB_CACHE.pop(COUPLE_ALL_KEY, None)
    except Exception as e:
        print(f"Error removing couple: {e}")

async def get_all_couples() -> List[Dict[str, Any]]:
    """Get all saved couples from the database with caching."""
    # Check cache first
    if COUPLE_ALL_KEY in DB_CACHE:
        return DB_CACHE[COUPLE_ALL_KEY]
    
    try:
        # Get from database
        couples = await couple_collection.find().to_list(length=1000)
        
        # Update cache
        DB_CACHE[COUPLE_ALL_KEY] = couples
        
        # Also update individual chat caches
        for couple in couples:
            if "chat_id" in couple:
                DB_CACHE[COUPLE_CHAT_KEY.format(couple["chat_id"])] = couple
                
        return couples
    except Exception as e:
        print(f"Error getting all couples: {e}")
        return []

async def save_waifu(chat_id: int, user_id: int, user_first_name: str, bond: str, waifu_id: int, waifu_first_name: str, waifu_photo: str = None) -> None:
    """Save the waifu details in the database for a specific chat and user with caching."""
    try:
        # Get current date in IST
        date_chosen = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare data
        data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "user_first_name": user_first_name,
            "waifu_id": waifu_id,
            "waifu_first_name": waifu_first_name,
            "waifu_photo": waifu_photo,
            "bond": bond,
            "date": date_chosen
        }
        
        # Update database
        await waifu_collection.update_one(
            {"chat_id": chat_id, "user_id": user_id},  # Use both chat_id and user_id as unique identifiers
            {"$set": data},
            upsert=True  # Insert a new document if none exists
        )
        
        # Update cache
        DB_CACHE[WAIFU_USER_KEY.format(user_id)] = data
    except Exception as e:
        print(f"Error saving waifu: {e}")

async def is_waifu_already_chosen(user_id: int) -> bool:
    """Check if a waifu is already chosen for the given user with caching."""
    try:
        # Get waifu with caching
        waifu = await get_waifu(user_id)
        return waifu is not None
    except Exception as e:
        print(f"Error checking if waifu is already chosen: {e}")
        return False

async def get_waifu(user_id: int) -> Optional[Dict[str, Any]]:
    """Get the waifu details for the given user with caching."""
    cache_key = WAIFU_USER_KEY.format(user_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        waifu = await waifu_collection.find_one({"user_id": user_id})
        
        # Update cache
        if waifu:
            DB_CACHE[cache_key] = waifu
            
        return waifu
    except Exception as e:
        print(f"Error getting waifu: {e}")
        return None
