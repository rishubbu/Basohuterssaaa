from pyrogram.types import Message, CallbackQuery, ChatMember
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from functools import wraps, lru_cache
from Yumeko import app, admin_cache, log
from pyrogram.errors import RPCError
import json
import asyncio
from Yumeko.yumeko import USER_NOT_ADMIN

# Cache for sudoers to avoid repeated file reads
_SUDOERS_CACHE = None
_PRIVILEGED_USERS_CACHE = None
_LAST_CACHE_UPDATE = 0
_CACHE_LOCK = asyncio.Lock()

@lru_cache(maxsize=1)
def load_sudoers():
    """Load the sudoers.json file with caching."""
    try:
        with open("sudoers.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log.warning("Failed to load sudoers.json, using empty defaults")
        return {"Hokages": [], "Jonins": [], "Chunins": []}

@lru_cache(maxsize=1)
def get_privileged_users():
    """Combine all privileged user IDs into one list with caching."""
    sudoers = load_sudoers()
    return frozenset(
        sudoers.get("Hokages", []) +
        sudoers.get("Jonins", []) +
        sudoers.get("Chunins", [])
    )

async def cache_all_admin(chat_id):
    """Efficiently cache all admins for a chat."""
    try:
        # Use async context manager to ensure proper resource handling
        async with _CACHE_LOCK:
            # Check if we already have recent data for this chat
            if chat_id in admin_cache.get("_chat_last_update", {}):
                if admin_cache["_chat_last_update"][chat_id] > asyncio.get_event_loop().time() - 300:  # 5 min cache
                    return
            
            # Initialize chat update tracking if needed
            if "_chat_last_update" not in admin_cache:
                admin_cache["_chat_last_update"] = {}
            
            # Fetch all administrators in the chat in one API call
            admins = []
            async for admin in app.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
                admins.append(admin)
            
            # Batch update the cache
            for admin in admins:
                user_id = admin.user.id
                # Extract and cache privileges directly from the admin object
                privileges = {
                    "is_admin": True,  # We know they're admin since we filtered for ADMINISTRATORS
                    "is_owner": admin.status == ChatMemberStatus.OWNER,
                    "privileges": admin.privileges if hasattr(admin, 'privileges') else None,
                }
                admin_cache[(chat_id, user_id)] = privileges
            
            # Update the last refresh time for this chat
            admin_cache["_chat_last_update"][chat_id] = asyncio.get_event_loop().time()
    except Exception as e:
        log.error(f"Error caching admins for chat {chat_id}: {e}")

async def fetch_admin_privileges(chat_id, user_id):
    """Fetch admin privileges from the Telegram API and cache them."""
    try:
        # Check if we need to refresh the entire admin list
        await cache_all_admin(chat_id)
        return admin_cache.get((chat_id, user_id))
    except Exception as e:
        log.error(f"Error fetching admin privileges: {e}")
        return None

async def check_admin_status(chat_id, user_id):
    """Efficiently check if a user is an admin with caching."""
    # Check if user is in privileged users (sudoers)
    if user_id in get_privileged_users():
        return {"is_admin": True, "is_owner": True, "privileges": None}
    
    # Check cache first
    cached_privileges = admin_cache.get((chat_id, user_id))
    if cached_privileges:
        return cached_privileges
    
    # If not in cache, fetch individual status (faster than fetching all admins)
    try:
        member = await app.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        is_owner = member.status == ChatMemberStatus.OWNER
        
        # Cache the result
        privileges = {
            "is_admin": is_admin,
            "is_owner": is_owner,
            "privileges": member.privileges if hasattr(member, 'privileges') else None
        }
        admin_cache[(chat_id, user_id)] = privileges
        return privileges
    except Exception as e:
        log.error(f"Error checking admin status: {e}")
        return {"is_admin": False, "is_owner": False, "privileges": None}

def ensure_privilege(privilege_name):
    """Decorator to ensure user has specific admin privilege."""
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update, *args, **kwargs):
            # Extract user and chat info
            if isinstance(update, Message):
                if not update.from_user:
                    return
                user_id = update.from_user.id
                chat_id = update.chat.id
            elif isinstance(update, CallbackQuery):
                if not update.from_user or not update.message:
                    return
                user_id = update.from_user.id
                chat_id = update.message.chat.id
            else:
                return

            # Fast path for privileged users
            if user_id in get_privileged_users():
                return await func(client, update, *args, **kwargs)

            # Check admin status
            admin_status = await check_admin_status(chat_id, user_id)
            
            # If not admin, reject
            if not admin_status["is_admin"]:
                if isinstance(update, Message):
                    await update.reply(USER_NOT_ADMIN)
                elif isinstance(update, CallbackQuery):
                    await update.answer(USER_NOT_ADMIN, show_alert=True)
                return

            # Check specific privilege
            privileges_obj = admin_status.get("privileges")
            if not privileges_obj or not getattr(privileges_obj, privilege_name, False):
                if isinstance(update, Message):
                    await update.reply(f"𝖸𝗈𝗎 𝖭𝖾𝖾𝖽 𝖳𝗁𝖾 `{privilege_name}` 𝖯𝗋𝗂𝗏𝗂𝗅𝖾𝗀𝖾 𝖳𝗈 𝖴𝗌𝖾 𝖳𝗁𝗂𝗌 𝖢𝗈𝗆𝗆𝖺𝗇𝖽.")
                elif isinstance(update, CallbackQuery):
                    await update.answer(f"𝖸𝗈𝗎 𝖭𝖾𝖾𝖽 𝖳𝗁𝖾 '{privilege_name}' 𝖯𝗋𝗂𝗏𝗂𝗅𝖾𝗀𝖾 𝖳𝗈 𝖴𝗌𝖾 𝖳𝗁𝗂𝗌.", show_alert=True)
                return

            return await func(client, update, *args, **kwargs)
        return wrapper
    return decorator

def ensure_admin_or_owner(required_role=None):
    """
    Ensure the user is an admin or owner with optimized checking.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(client, update, *args, **kwargs):
            # Extract user and chat info
            if isinstance(update, Message):
                if not update.from_user:
                    return
                user_id = update.from_user.id
                chat_id = update.chat.id
            elif isinstance(update, CallbackQuery):
                if not update.from_user or not update.message:
                    return
                user_id = update.from_user.id
                chat_id = update.message.chat.id
            else:
                return

            # Fast path for privileged users
            if user_id in get_privileged_users():
                return await func(client, update, *args, **kwargs)

            try:
                # Check admin status efficiently
                admin_status = await check_admin_status(chat_id, user_id)
                
                # If not admin, reject
                if not admin_status["is_admin"]:
                    if isinstance(update, Message):
                        await update.reply(USER_NOT_ADMIN)
                    elif isinstance(update, CallbackQuery):
                        await update.answer(USER_NOT_ADMIN, show_alert=True)
                    return

                # Check owner status if required
                if required_role == "owner" and not admin_status["is_owner"]:
                    if isinstance(update, Message):
                        await update.reply("𝖸𝗈𝗎 𝖬𝗎𝗌𝗍 𝖡𝖾 𝖳𝗁𝖾 𝖢𝗁𝖺𝗍 𝖮𝗐𝗇𝖾𝗋 𝖳𝗈 𝖴𝗌𝖾 𝖳𝗁𝗂𝗌 𝖢𝗈𝗆𝗆𝖺𝗇𝖽.")
                    elif isinstance(update, CallbackQuery):
                        await update.answer("𝖸𝗈𝗎 𝖬𝗎𝗌𝗍 𝖡𝖾 𝖳𝗁𝖾 𝖢𝗁𝖺𝗍 𝖮𝗐𝗇𝖾𝗋 𝖳𝗈 𝖴𝗌𝖾 𝖳𝗁𝗂𝗌.", show_alert=True)
                    return

                return await func(client, update, *args, **kwargs)

            except RPCError as e:
                log.info(f"Failed to verify privileges: {e}")
                return

        return wrapper
    return decorator

# Convenience decorators
def can_manage_chat(func):
    return ensure_privilege("can_manage_chat")(func)

def can_delete_messages(func):
    return ensure_privilege("can_delete_messages")(func)

def can_manage_video_chats(func):
    return ensure_privilege("can_manage_video_chats")(func)

def can_restrict_members(func):
    return ensure_privilege("can_restrict_members")(func)

def can_promote_members(func):
    return ensure_privilege("can_promote_members")(func)

def can_change_info(func):
    return ensure_privilege("can_change_info")(func)

def can_post_messages(func):
    return ensure_privilege("can_post_messages")(func)

def can_edit_messages(func):
    return ensure_privilege("can_edit_messages")(func)

def can_invite_users(func):
    return ensure_privilege("can_invite_users")(func)

def can_pin_messages(func):
    return ensure_privilege("can_pin_messages")(func)

def is_anonymous(func):
    return ensure_privilege("is_anonymous")(func)

def chatadmin(func):
    return ensure_admin_or_owner(required_role="admin")(func)

def chatowner(func):
    return ensure_admin_or_owner(required_role="owner")(func)

