from Yumeko.database import approved_collection, DB_CACHE, PERSISTENT_CACHE, _cache_lock
import asyncio
from functools import lru_cache

# Cache TTL in seconds
APPROVE_CACHE_TTL = 300  # 5 minutes

# Cache for approved users by chat_id
_approved_users_cache = {}
_approved_users_expiry = {}

# Cache for individual user approval status
_user_approval_cache = {}
_user_approval_expiry = {}

async def get_approved_users(chat_id: int):
    """Get the list of approved users for a specific chat with caching."""
    # Check if we have a valid cache entry
    current_time = asyncio.get_event_loop().time()
    cache_key = f"approved_users:{chat_id}"
    
    if cache_key in _approved_users_cache and _approved_users_expiry.get(cache_key, 0) > current_time:
        return _approved_users_cache[cache_key]
    
    # If not in cache or expired, fetch from database
    approved_users = await approved_collection.find({"chat_id": chat_id}).to_list(length=None)
    result = [(user['user_id'], user['user_name']) for user in approved_users]
    
    # Update cache
    _approved_users_cache[cache_key] = result
    _approved_users_expiry[cache_key] = current_time + APPROVE_CACHE_TTL
    
    return result

async def is_user_approved(chat_id: int, user_id: int):
    """Check if a user is approved in the given chat with caching."""
    # Check if we have a valid cache entry
    current_time = asyncio.get_event_loop().time()
    cache_key = f"is_approved:{chat_id}:{user_id}"
    
    if cache_key in _user_approval_cache and _user_approval_expiry.get(cache_key, 0) > current_time:
        return _user_approval_cache[cache_key]
    
    # If not in cache or expired, fetch from database
    user = await approved_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    result = user is not None
    
    # Update cache
    _user_approval_cache[cache_key] = result
    _user_approval_expiry[cache_key] = current_time + APPROVE_CACHE_TTL
    
    return result

async def approve_user(chat_id: int, user_id: int, user_name: str):
    """Approve a user in the given chat with cache invalidation."""
    # Check if already approved (using cache)
    if await is_user_approved(chat_id, user_id):
        return False  # User is already approved
    
    # Update database
    await approved_collection.insert_one({"chat_id": chat_id, "user_id": user_id, "user_name": user_name})
    
    # Invalidate caches
    _invalidate_approval_cache(chat_id, user_id)
    
    return True

async def unapprove_user(chat_id: int, user_id: int):
    """Unapprove a user in the given chat with cache invalidation."""
    # Update database
    await approved_collection.delete_one({"chat_id": chat_id, "user_id": user_id})
    
    # Invalidate caches
    _invalidate_approval_cache(chat_id, user_id)

async def unapprove_all_users(chat_id: int):
    """Unapprove all users in the given chat with cache invalidation."""
    # Update database
    await approved_collection.delete_many({"chat_id": chat_id})
    
    # Invalidate caches
    _invalidate_all_approval_cache(chat_id)

def _invalidate_approval_cache(chat_id: int, user_id: int):
    """Invalidate approval caches for a specific user and chat."""
    # Invalidate user approval cache
    cache_key = f"is_approved:{chat_id}:{user_id}"
    if cache_key in _user_approval_cache:
        del _user_approval_cache[cache_key]
    if cache_key in _user_approval_expiry:
        del _user_approval_expiry[cache_key]
    
    # Invalidate approved users list cache
    cache_key = f"approved_users:{chat_id}"
    if cache_key in _approved_users_cache:
        del _approved_users_cache[cache_key]
    if cache_key in _approved_users_expiry:
        del _approved_users_expiry[cache_key]

def _invalidate_all_approval_cache(chat_id: int):
    """Invalidate all approval caches for a specific chat."""
    # Find and remove all cache entries for this chat
    user_keys_to_remove = [k for k in _user_approval_cache.keys() if k.startswith(f"is_approved:{chat_id}:")]
    for k in user_keys_to_remove:
        if k in _user_approval_cache:
            del _user_approval_cache[k]
        if k in _user_approval_expiry:
            del _user_approval_expiry[k]
    
    # Invalidate approved users list cache
    cache_key = f"approved_users:{chat_id}"
    if cache_key in _approved_users_cache:
        del _approved_users_cache[cache_key]
    if cache_key in _approved_users_expiry:
        del _approved_users_expiry[cache_key]

# Batch operations for efficiency
async def approve_multiple_users(chat_id: int, users: list):
    """
    Approve multiple users in a chat in a single operation.
    
    Args:
        chat_id: The chat ID
        users: List of (user_id, user_name) tuples
    """
    if not users:
        return
    
    # Prepare documents for bulk insert
    documents = [
        {"chat_id": chat_id, "user_id": user_id, "user_name": user_name}
        for user_id, user_name in users
    ]
    
    # Insert all documents
    await approved_collection.insert_many(documents)
    
    # Invalidate cache
    _invalidate_all_approval_cache(chat_id)

async def get_approval_count(chat_id: int = None):
    """
    Get the count of approved users, optionally filtered by chat.
    
    Args:
        chat_id: Optional chat ID to filter by
        
    Returns:
        The count of approved users
    """
    # Create a cache key
    cache_key = f"approval_count:{chat_id or 'all'}"
    
    # Check if we have this in the persistent cache
    async with _cache_lock:
        if cache_key in PERSISTENT_CACHE:
            return PERSISTENT_CACHE[cache_key]
    
    # If not in cache, fetch from database
    query = {"chat_id": chat_id} if chat_id else {}
    count = await approved_collection.count_documents(query)
    
    # Update cache
    async with _cache_lock:
        PERSISTENT_CACHE[cache_key] = count
    
    return count
