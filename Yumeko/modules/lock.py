from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from Yumeko import app, LOCK_GROUP
from Yumeko.database.lockdb import (
    set_lock,
    unset_lock,
    get_locks,
)
from Yumeko.database.approve_db import is_user_approved
from Yumeko.helper.lock_helper import  LOCKABLES
from Yumeko.decorator.chatadmin import chatadmin, check_admin_status
import re
from functools import lru_cache
from pyrogram.enums import ParseMode

# Helper functions with caching for better performance
@lru_cache(maxsize=128)
def contains_rtl(text):
    """Check if text contains RTL characters with caching."""
    return any(ord(c) in range(0x0590, 0x08FF) for c in text)

@lru_cache(maxsize=128)
def contains_cjk(text):
    """Check if text contains CJK characters with caching."""
    return any(ord(c) >= 0x4E00 and ord(c) <= 0x9FFF for c in text)

@lru_cache(maxsize=128)
def contains_cyrillic(text):
    """Check if text contains Cyrillic characters with caching."""
    return any(ord(c) in range(0x0400, 0x04FF) for c in text)

@lru_cache(maxsize=128)
def contains_emoji(text):
    """Check if text contains emoji characters with caching."""
    return any(ord(c) > 0x1F600 for c in text if ord(c) < 0x1F64F)

# Precompile regex patterns for better performance
URL_PATTERN = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\+?[0-9\s\-\(\)]+")
INVITE_LINK_PATTERN = re.compile(r"https://t\.me/\+[a-zA-Z0-9_-]+")

@app.on_message(filters.command("lock") & filters.group)
@chatadmin
async def lock_command(client, message: Message):
    """Handle /lock command to enable locks."""
    chat_id = message.chat.id
    
    # Get lock types from command
    if len(message.command) < 2:
        await message.reply_text("⚙️ **Usage:** Specify the lock type(s) to enable.\n"
                                "Example: `/lock all` or `/lock audio video`", parse_mode=ParseMode.MARKDOWN)
        return
    
    lock_types = [lock_type.lower() for lock_type in message.command[1:]]
    
    # Validate lock types
    invalid_types = [lt for lt in lock_types if lt not in LOCKABLES]
    if invalid_types:
        await message.reply_text(f"⚠️ Invalid lock type(s): `{', '.join(invalid_types)}`\n"
                                f"Use `/locktypes` to view available lock types.", parse_mode=ParseMode.MARKDOWN)
        return
    
    # Apply locks
    for lock_type in lock_types:
        await set_lock(chat_id, lock_type)
        
        # If "all" is locked, set chat permissions
        if lock_type == "all":
            permissions = ChatPermissions(all_perms=False)
            await app.set_chat_permissions(chat_id, permissions)
    
    await message.reply_text(f"🔒 **Locked:** {', '.join(lock_types)}", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("unlock") & filters.group)
@chatadmin
async def unlock_command(client, message: Message):
    """Handle /unlock command to disable locks."""
    chat_id = message.chat.id
    
    # Get lock types from command
    if len(message.command) < 2:
        await message.reply_text("⚙️ **Usage:** Specify the lock type(s) to disable.\n"
                                "Example: `/unlock all` or `/unlock audio video`", parse_mode=ParseMode.MARKDOWN)
        return
    
    lock_types = [lock_type.lower() for lock_type in message.command[1:]]
    
    # Validate lock types
    invalid_types = [lt for lt in lock_types if lt not in LOCKABLES]
    if invalid_types:
        await message.reply_text(f"⚠️ Invalid unlock type(s): `{', '.join(invalid_types)}`\n"
                                f"Use `/locktypes` to view available lock types.", parse_mode=ParseMode.MARKDOWN)
        return
    
    # Apply unlocks
    for lock_type in lock_types:
        await unset_lock(chat_id, lock_type)
        
        # If "all" is unlocked, set chat permissions
        if lock_type == "all":
            permissions = ChatPermissions(all_perms=True)
            await app.set_chat_permissions(chat_id, permissions)
    
    await message.reply_text(f"🔓 **Unlocked:** {', '.join(lock_types)}", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("locktypes") & filters.group)
async def locktypes_command(client, message: Message):
    """Handle /locktypes to list all lockable types with inline buttons."""
    lockables = list(LOCKABLES.items())
    
    # Create rows of 3 buttons each
    keyboard = []
    row = []
    
    for i, (lock_type, description) in enumerate(lockables):
        row.append(InlineKeyboardButton(
            text=lock_type.capitalize(),
            callback_data=f"locktype_{lock_type}"
        ))
        
        # Create a new row after every 3 buttons
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    
    # Add any remaining buttons
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        "📜 **Available Lock Types:**\nTap a button to view the description.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_callback_query(filters.regex(r"^locktype_(.+)"))
async def locktype_description(client, callback_query: CallbackQuery):
    """Show lock type description when an inline button is clicked."""
    # Extract lock type from callback data
    lock_type = callback_query.data.split("_", 1)[1]
    description = LOCKABLES.get(lock_type, "No description available.")
    
    await callback_query.answer(
        text=f"🔒 {lock_type.capitalize()} Lock:\n{description}",
        show_alert=True
    )

@app.on_message(filters.command("locks") & filters.group)
async def locks_command(client, message: Message):
    """Handle /locks to view active locks in the chat."""
    chat_id = message.chat.id
    locks = await get_locks(chat_id)
    
    if not locks:
        await message.reply_text("🔓 **No locks are currently enabled in this chat.**", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text(f"🔒 **Active Locks:*\n`{', '.join(locks)}`**", parse_mode=ParseMode.MARKDOWN)

async def is_user_admin_or_approved(chat_id: int, user_id: int) -> bool:
    """Check if a user is an admin or approved in a chat with optimized caching."""
    # Check if user is approved first (faster than admin check)
    if await is_user_approved(chat_id, user_id):
        return True
    
    # Use the optimized admin check function
    admin_status = await check_admin_status(chat_id, user_id)
    return admin_status.get("is_admin", False)

# Cache for active locks to reduce database queries
_locks_cache = {}
_locks_cache_ttl = {}
_LOCKS_CACHE_DURATION = 5  # 60 seconds TTL

import time

async def get_cached_locks(chat_id: int):
    """Get locks with caching to reduce database queries."""
    current_time = time.time()  # Use standard time module instead
    
    # Check if we have a valid cache
    if chat_id in _locks_cache and _locks_cache_ttl.get(chat_id, 0) > current_time:
        return _locks_cache[chat_id]
    
    # If not in cache or expired, fetch from database
    locks = await get_locks(chat_id)
    
    # Update cache
    _locks_cache[chat_id] = locks
    _locks_cache_ttl[chat_id] = current_time + _LOCKS_CACHE_DURATION
    
    return locks

@app.on_message(filters.group & ~filters.service, group=LOCK_GROUP)
async def message_handler(client, message: Message):
    """Delete messages violating locks."""
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None
    
    # Skip processing if no user
    if not user_id:
        return
    
    # Get active locks (with caching)
    locks = await get_cached_locks(chat_id)
    if not locks:
        return
    
    # Check if user is admin or approved
    if await is_user_admin_or_approved(chat_id, user_id):
        return
    
    # Initialize deletion flag
    to_delete = False
    
    # Check lock conditions
    if "all" in locks:
        to_delete = True
    
    # Check media locks
    elif any(lock in locks for lock in ["album", "audio", "document", "photo", "video", "videonote", "voice", "animation", "sticker"]):
        if ("album" in locks and message.media_group_id) or \
           ("audio" in locks and message.audio) or \
           ("document" in locks and message.document) or \
           ("photo" in locks and message.photo) or \
           ("video" in locks and message.video) or \
           ("videonote" in locks and message.video_note) or \
           ("voice" in locks and message.voice) or \
           ("gif" in locks and message.animation) or \
           ("sticker" in locks and message.sticker) or \
           ("animated_sticker" in locks and message.sticker and message.sticker.is_animated) or \
           ("premium_sticker" in locks and message.sticker and message.sticker.premium):
            to_delete = True
    
    # Check bot and inline locks
    elif any(lock in locks for lock in ["bot", "botlink", "inline"]):
        if ("bot" in locks and message.via_bot) or \
           ("botlink" in locks and message.text and "@" in message.text and "bot" in message.text.lower()) or \
           ("inline" in locks and message.via_bot):
            to_delete = True
    
    # Check text content locks
    elif message.text and any(lock in locks for lock in ["text", "command", "url", "email", "phone", "invitelink", "rtl", "cjk", "cyrillic", "emoji"]):
        text = message.text
        
        if ("text" in locks) or \
           ("command" in locks and text.startswith("/")) or \
           ("url" in locks and URL_PATTERN.search(text)) or \
           ("email" in locks and EMAIL_PATTERN.search(text)) or \
           ("phone" in locks and PHONE_PATTERN.search(text)) or \
           ("invitelink" in locks and ("t.me/" in text or "telegram.me/" in text or INVITE_LINK_PATTERN.search(text))) or \
           ("rtl" in locks and contains_rtl(text)) or \
           ("cjk" in locks and contains_cjk(text)) or \
           ("cyrillic" in locks and contains_cyrillic(text)) or \
           ("emoji" in locks and contains_emoji(text)):
            to_delete = True
    
    # Check other locks
    elif ("anonchannel" in locks and message.sender_chat and not message.is_topic_message) or \
         ("btn" in locks and message.reply_markup) or \
         ("contact" in locks and message.contact) or \
         ("dice" in locks and message.dice) or \
         ("forward" in locks and message.forward_date) or \
         ("game" in locks and message.game) or \
         ("location" in locks and message.location) or \
         ("poll" in locks and message.poll):
        to_delete = True
    
    # Delete message if it violates any lock
    if to_delete:
        try:
            await message.delete()
        except Exception:
            pass


__module__ = "𝖫𝗈𝖼𝗄𝗌"

__help__ = """🔒 **𝖫𝗈𝖼𝗄𝗌 𝖬𝗈𝖽𝗎𝗅𝖾**:
𝖬𝖺𝗇𝖺𝗀𝖾 𝖼𝗁𝖺𝗍 𝗋𝖾𝗌𝗍𝗋𝗂𝖼𝗍𝗂𝗈𝗇𝗌 𝖾𝖿𝖿𝖾𝖼𝗍𝗂𝗏𝖾𝗅𝗒. 𝖫𝗈𝖼𝗄 𝗈𝗋 𝗎𝗇𝗅𝗈𝖼𝗄 𝗏𝖺𝗋𝗂𝗈𝗎𝗌 𝗍𝗒𝗉𝖾𝗌 𝗈𝖿 𝖼𝗈𝗇𝗍𝖾𝗇𝗍 𝗂𝗇 𝗍𝗁𝖾 𝖼𝗁𝖺𝗍.
 
**𝖠𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌**:
- `/𝗅𝗈𝖼𝗄 <𝗍𝗒𝗉𝖾(𝗌)>` - 𝖤𝗇𝖺𝖻𝗅𝖾 𝗅𝗈𝖼𝗄𝗌 𝖿𝗈𝗋 𝗌𝗉𝖾𝖼𝗂𝖿𝗂𝖼 𝖼𝗈𝗇𝗍𝖾𝗇𝗍 𝗍𝗒𝗉𝖾𝗌 (𝖾.𝗀., `/𝗅𝗈𝖼𝗄 𝗉𝗁𝗈𝗍𝗈`).
   - 𝖴𝗌𝖾 `/𝗅𝗈𝖼𝗄 𝖺𝗅𝗅` 𝗍𝗈 𝖾𝗇𝖺𝖻𝗅𝖾 𝖺𝗅𝗅 𝗅𝗈𝖼𝗄𝗌.
 - `/𝗎𝗇𝗅𝗈𝖼𝗄 <𝗍𝗒𝗉𝖾(𝗌)>` - 𝖣𝗂𝗌𝖺𝖻𝗅𝖾 𝗅𝗈𝖼𝗄𝗌 𝖿𝗈𝗋 𝗌𝗉𝖾𝖼𝗂𝖿𝗂𝖼 𝖼𝗈𝗇𝗍𝖾𝗇𝗍 𝗍𝗒𝗉𝖾𝗌 (𝖾.𝗀., `/𝗎𝗇𝗅𝗈𝖼𝗄 𝗏𝗂𝖽𝖾𝗈`).
   - 𝖴𝗌𝖾 `/𝗎𝗇𝗅𝗈𝖼𝗄 𝖺𝗅𝗅` 𝗍𝗈 𝖽𝗂𝗌𝖺𝖻𝗅𝖾 𝖺𝗅𝗅 𝗅𝗈𝖼𝗄𝗌.
 - `/𝗅𝗈𝖼𝗄𝗍𝗒𝗉𝖾𝗌` - 𝖵𝗂𝖾𝗐 𝖺𝗅𝗅 𝗅𝗈𝖼𝗄𝖺𝖻𝗅𝖾 𝖼𝗈𝗇𝗍𝖾𝗇𝗍 𝗍𝗒𝗉𝖾𝗌 𝖺𝗇𝖽 𝗍𝗁𝖾𝗂𝗋 𝖽𝖾𝗌𝖼𝗋𝗂𝗉𝗍𝗂𝗈𝗇𝗌.
 - `/𝗅𝗈𝖼𝗄𝗌` - 𝖢𝗁𝖾𝖼𝗄 𝖼𝗎𝗋𝗋𝖾𝗇𝗍𝗅𝗒 𝖺𝖼𝗍𝗂𝗏𝖾 𝗅𝗈𝖼𝗄𝗌 𝗂𝗇 𝗍𝗁𝖾 𝖼𝗁𝖺𝗍.
 
**𝖴𝗌𝖺𝗀𝖾 𝖤𝗑𝖺𝗆𝗉𝗅𝖾𝗌**:
- `/𝗅𝗈𝖼𝗄 𝗉𝗁𝗈𝗍𝗈 𝗏𝗂𝖽𝖾𝗈` - 𝖱𝖾𝗌𝗍𝗋𝗂𝖼𝗍 𝗎𝗌𝖾𝗋𝗌 𝖿𝗋𝗈𝗆 𝗌𝖾𝗇𝖽𝗂𝗇𝗀 𝗉𝗁𝗈𝗍𝗈𝗌 𝖺𝗇𝖽 𝗏𝗂𝖽𝖾𝗈𝗌.
 - `/𝗎𝗇𝗅𝗈𝖼𝗄 𝗍𝖾𝗑𝗍 𝖼𝗈𝗆𝗆𝖺𝗇𝖽` - 𝖠𝗅𝗅𝗈𝗐 𝗍𝖾𝗑𝗍 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝖺𝗇𝖽 𝖼𝗈𝗆𝗆𝖺𝗇𝖽𝗌.
 
"""

