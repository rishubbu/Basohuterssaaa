from Yumeko.database import gmute_collection, gban_collection, banned_chats, DB_CACHE
from typing import Optional, Dict, Any, List
import asyncio

# Cache keys
GMUTE_USER_KEY = "gmute_user_{}"
GBAN_USER_KEY = "gban_user_{}"
BANNED_CHATS_USER_KEY = "banned_chats_user_{}"
ALL_GMUTED_USERS_KEY = "all_gmuted_users"
ALL_GBANNED_USERS_KEY = "all_gbanned_users"
TOTAL_GMUTED_USERS_KEY = "total_gmuted_users"
TOTAL_GBANNED_USERS_KEY = "total_gbanned_users"

async def add_to_gmute(user_id: int, first_name: str = None, username: str = None) -> Dict[str, Any]:
    """
    Add a user to the GMute collection with caching.
    """
    try:
        # Prepare data
        data = {
            "id": user_id,
            "first_name": first_name,
            "username": username,
        }
        
        # Update database
        await gmute_collection.update_one({"id": user_id}, {"$set": data}, upsert=True)
        
        # Update cache
        DB_CACHE[GMUTE_USER_KEY.format(user_id)] = data
        
        # Invalidate related caches
        DB_CACHE.pop(ALL_GMUTED_USERS_KEY, None)
        DB_CACHE.pop(TOTAL_GMUTED_USERS_KEY, None)
        
        return data
    except Exception as e:
        print(f"Error adding user to gmute: {e}")
        return {"id": user_id, "error": str(e)}

async def add_to_gban(user_id: int, first_name: str = None, username: str = None) -> Dict[str, Any]:
    """
    Add a user to the GBan collection with caching.
    """
    try:
        # Prepare data
        data = {
            "id": user_id,
            "first_name": first_name,
            "username": username,
        }
        
        # Update database
        await gban_collection.update_one({"id": user_id}, {"$set": data}, upsert=True)
        
        # Update cache
        DB_CACHE[GBAN_USER_KEY.format(user_id)] = data
        
        # Invalidate related caches
        DB_CACHE.pop(ALL_GBANNED_USERS_KEY, None)
        DB_CACHE.pop(TOTAL_GBANNED_USERS_KEY, None)
        
        return data
    except Exception as e:
        print(f"Error adding user to gban: {e}")
        return {"id": user_id, "error": str(e)}

async def remove_from_gmute(user_id: int) -> bool:
    """
    Remove a user from the GMute collection with cache invalidation.
    """
    try:
        # Delete from database
        result = await gmute_collection.delete_one({"id": user_id})
        
        # Invalidate caches
        DB_CACHE.pop(GMUTE_USER_KEY.format(user_id), None)
        DB_CACHE.pop(ALL_GMUTED_USERS_KEY, None)
        DB_CACHE.pop(TOTAL_GMUTED_USERS_KEY, None)
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error removing user from gmute: {e}")
        return False

async def remove_from_gban(user_id: int) -> bool:
    """
    Remove a user from the GBan collection with cache invalidation.
    """
    try:
        # Delete from database
        result = await gban_collection.delete_one({"id": user_id})
        
        # Invalidate caches
        DB_CACHE.pop(GBAN_USER_KEY.format(user_id), None)
        DB_CACHE.pop(ALL_GBANNED_USERS_KEY, None)
        DB_CACHE.pop(TOTAL_GBANNED_USERS_KEY, None)
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error removing user from gban: {e}")
        return False

async def get_all_gmuted_users() -> List[Dict[str, Any]]:
    """
    Get all users in the GMute collection with caching.
    """
    # Check cache first
    if ALL_GMUTED_USERS_KEY in DB_CACHE:
        return DB_CACHE[ALL_GMUTED_USERS_KEY]
    
    try:
        # Get from database
        users = await gmute_collection.find().to_list(length=None)
        
        # Update cache
        DB_CACHE[ALL_GMUTED_USERS_KEY] = users
        
        # Also update individual user caches
        for user in users:
            if "id" in user:
                DB_CACHE[GMUTE_USER_KEY.format(user["id"])] = user
                
        return users
    except Exception as e:
        print(f"Error getting all gmuted users: {e}")
        return []

async def get_all_gbanned_users() -> List[Dict[str, Any]]:
    """
    Get all users in the GBan collection with caching.
    """
    # Check cache first
    if ALL_GBANNED_USERS_KEY in DB_CACHE:
        return DB_CACHE[ALL_GBANNED_USERS_KEY]
    
    try:
        # Get from database
        users = await gban_collection.find().to_list(length=None)
        
        # Update cache
        DB_CACHE[ALL_GBANNED_USERS_KEY] = users
        
        # Also update individual user caches
        for user in users:
            if "id" in user:
                DB_CACHE[GBAN_USER_KEY.format(user["id"])] = user
                
        return users
    except Exception as e:
        print(f"Error getting all gbanned users: {e}")
        return []

async def is_user_gmuted(user_id: int) -> bool:
    """
    Check if a user is in the GMute collection with caching.
    """
    cache_key = GMUTE_USER_KEY.format(user_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return True
    
    try:
        # Get from database
        user = await gmute_collection.find_one({"id": user_id})
        
        # Update cache
        if user:
            DB_CACHE[cache_key] = user
            
        return user is not None
    except Exception as e:
        print(f"Error checking if user is gmuted: {e}")
        return False

async def is_user_gbanned(user_id: int) -> bool:
    """
    Check if a user is in the GBan collection with caching.
    """
    cache_key = GBAN_USER_KEY.format(user_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return True
    
    try:
        # Get from database
        user = await gban_collection.find_one({"id": user_id})
        
        # Update cache
        if user:
            DB_CACHE[cache_key] = user
            
        return user is not None
    except Exception as e:
        print(f"Error checking if user is gbanned: {e}")
        return False

async def get_total_gbanned_users() -> int:
    """
    Get the total number of GBanned users with caching.
    """
    # Check cache first
    if TOTAL_GBANNED_USERS_KEY in DB_CACHE:
        return DB_CACHE[TOTAL_GBANNED_USERS_KEY]
    
    try:
        # Get from database
        count = await gban_collection.count_documents({})
        
        # Update cache
        DB_CACHE[TOTAL_GBANNED_USERS_KEY] = count
        
        return count
    except Exception as e:
        print(f"Error getting total gbanned users: {e}")
        return 0

async def get_total_gmuted_users() -> int:
    """
    Get the total number of GMute users with caching.
    """
    # Check cache first
    if TOTAL_GMUTED_USERS_KEY in DB_CACHE:
        return DB_CACHE[TOTAL_GMUTED_USERS_KEY]
    
    try:
        # Get from database
        count = await gmute_collection.count_documents({})
        
        # Update cache
        DB_CACHE[TOTAL_GMUTED_USERS_KEY] = count
        
        return count
    except Exception as e:
        print(f"Error getting total gmuted users: {e}")
        return 0

async def save_banned_chats(user_id: int, chat_ids) -> Dict[str, Any]:
    """
    Save the list of chat IDs where the user was banned with caching.
    Handles both a single chat ID and a list of chat IDs.
    """
    try:
        # Ensure chat_ids is a list
        if isinstance(chat_ids, int):
            chat_ids = [chat_ids]

        # Get existing data with caching
        existing_chats = await get_banned_chats(user_id)

        # Combine and remove duplicates
        updated_chats = list(set(existing_chats + chat_ids))

        # Prepare data
        data = {
            "id": user_id,
            "banned_chats": updated_chats,
        }
        
        # Update database
        await banned_chats.update_one({"id": user_id}, {"$set": data}, upsert=True)
        
        # Update cache
        DB_CACHE[BANNED_CHATS_USER_KEY.format(user_id)] = updated_chats
        
        return data
    except Exception as e:
        print(f"Error saving banned chats: {e}")
        return {"id": user_id, "error": str(e)}

async def get_banned_chats(user_id: int) -> List[int]:
    """
    Retrieve the list of chat IDs where the user was banned with caching.
    """
    cache_key = BANNED_CHATS_USER_KEY.format(user_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        user_data = await banned_chats.find_one({"id": user_id})
        banned_chat_list = user_data.get("banned_chats", []) if user_data else []
        
        # Update cache
        DB_CACHE[cache_key] = banned_chat_list
        
        return banned_chat_list
    except Exception as e:
        print(f"Error getting banned chats: {e}")
        return []
