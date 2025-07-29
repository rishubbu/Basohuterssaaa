from Yumeko import app
from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus, ParseMode, ChatMembersFilter
from Yumeko.decorator.chatadmin import chatadmin
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save
from Yumeko.helper.log_helper import send_log, format_log
from config import config
import time
from Yumeko.database import db, DB_CACHE

# Create a collection for AntiBanAll
antibanall_collection = db.AntiBanAllSettings

# Cache for tracking ban actions
ban_tracker = {}
# TTL for ban tracking (10 seconds)
BAN_TRACKING_TTL = 10
# Threshold for number of bans to trigger action
BAN_THRESHOLD = 5

# Cache keys
ANTIBANALL_CHAT_KEY = "antibanall_chat_{}"
ANTIBANALL_ENABLED_CHATS_KEY = "antibanall_enabled_chats"

# Enable AntiBanAll for a chat
async def enable_antibanall(chat_id: int, chat_title: str, chat_username: str = None) -> None:
    """Enable AntiBanAll for a specific chat and save details."""
    try:
        # Prepare data
        chat_data = {
            "chat_id": chat_id,
            "antibanall_enabled": True,
            "chat_title": chat_title,
            "chat_username": chat_username,
        }
        
        # Update database
        await antibanall_collection.update_one(
            {"chat_id": chat_id},
            {"$set": chat_data},
            upsert=True
        )
        
        # Update cache
        DB_CACHE[ANTIBANALL_CHAT_KEY.format(chat_id)] = chat_data
        
        # Invalidate enabled chats cache
        DB_CACHE.pop(ANTIBANALL_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error enabling AntiBanAll: {e}")

# Disable AntiBanAll for a chat
async def disable_antibanall(chat_id: int) -> None:
    """Disable AntiBanAll for a specific chat."""
    try:
        # Update database
        await antibanall_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"antibanall_enabled": False}},
            upsert=True
        )
        
        # Update cache
        cache_key = ANTIBANALL_CHAT_KEY.format(chat_id)
        if cache_key in DB_CACHE:
            DB_CACHE[cache_key]["antibanall_enabled"] = False
        
        # Invalidate enabled chats cache
        DB_CACHE.pop(ANTIBANALL_ENABLED_CHATS_KEY, None)
    except Exception as e:
        print(f"Error disabling AntiBanAll: {e}")

# Check if AntiBanAll is enabled for a chat
async def is_antibanall_enabled(chat_id: int) -> bool:
    """Check if AntiBanAll is enabled for a specific chat with caching."""
    try:
        # Get chat info with caching
        chat_data = await get_chat_info(chat_id)
        return chat_data.get("antibanall_enabled", False) if chat_data else False
    except Exception as e:
        print(f"Error checking if AntiBanAll is enabled: {e}")
        return False

# Get chat info
async def get_chat_info(chat_id: int):
    """Retrieve information about a specific chat with caching."""
    cache_key = ANTIBANALL_CHAT_KEY.format(chat_id)
    
    # Check cache first
    if cache_key in DB_CACHE:
        return DB_CACHE[cache_key]
    
    try:
        # Get from database
        chat_data = await antibanall_collection.find_one({"chat_id": chat_id})
        
        # Update cache
        if chat_data:
            DB_CACHE[cache_key] = chat_data
            
        return chat_data
    except Exception as e:
        print(f"Error getting chat info: {e}")
        return None

# Command to toggle AntiBanAll status
@app.on_message(filters.command("antibanall", prefixes=config.COMMAND_PREFIXES) & filters.group)
@chatadmin
@error
@save
async def antibanall_handler(client: Client, message: Message):
    chat_id = message.chat.id
    
    if await is_antibanall_enabled(chat_id):
        await disable_antibanall(chat_id)
        await message.reply_text("**🔴 𝖠𝗇𝗍𝗂𝖡𝖺𝗇𝖠𝗅𝗅 𝗁𝖺𝗌 𝖻𝖾𝖾𝗇 𝖽𝗂𝗌𝖺𝖻𝗅𝖾𝖽 𝖿𝗈𝗋 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍.**")
    else:
        await enable_antibanall(chat_id, message.chat.title, message.chat.username)
        await message.reply_text("**🟢 𝖠𝗇𝗍𝗂𝖡𝖺𝗇𝖠𝗅𝗅 𝗁𝖺𝗌 𝖻𝖾𝖾𝗇 𝖾𝗇𝖺𝖻𝗅𝖾𝖽 𝖿𝗈𝗋 𝗍𝗁𝗂𝗌 𝖼𝗁𝖺𝗍.**\n\n𝖨 𝗐𝗂𝗅𝗅 𝖽𝖾𝗆𝗈𝗍𝖾 𝖺𝖽𝗆𝗂𝗇𝗌 𝗐𝗁𝗈 𝖻𝖺𝗇 𝗆𝗈𝗋𝖾 𝗍𝗁𝖺𝗇 5 𝗎𝗌𝖾𝗋𝗌 𝗂𝗇 10 𝗌𝖾𝖼𝗈𝗇𝖽𝗌.")
    
    # Log the command usage
    log_message = await format_log(
        action="Toggle AntiBanAll Command Used",
        chat=message.chat.title or str(chat_id),
        admin=message.from_user.mention
    )
    await send_log(chat_id, log_message)

# Function to track ban actions
def add_ban_action(chat_id, admin_id):
    """Track ban actions by admin in a chat"""
    current_time = time.time()
    
    # Initialize chat tracker if not exists
    if chat_id not in ban_tracker:
        ban_tracker[chat_id] = {}
    
    # Initialize admin tracker if not exists
    if admin_id not in ban_tracker[chat_id]:
        ban_tracker[chat_id][admin_id] = {"bans": [], "last_cleanup": current_time}
    
    # Clean up old ban records (older than TTL)
    ban_tracker[chat_id][admin_id]["bans"] = [
        ban_time for ban_time in ban_tracker[chat_id][admin_id]["bans"]
        if current_time - ban_time < BAN_TRACKING_TTL
    ]
    
    # Add current ban
    ban_tracker[chat_id][admin_id]["bans"].append(current_time)
    ban_tracker[chat_id][admin_id]["last_cleanup"] = current_time
    
    # Return the count of recent bans
    return len(ban_tracker[chat_id][admin_id]["bans"])

# Function to check if admin is mass banning
def is_mass_banning(chat_id, admin_id):
    """Check if admin is mass banning users"""
    if chat_id not in ban_tracker or admin_id not in ban_tracker[chat_id]:
        return False
    
    # Clean up old ban records
    current_time = time.time()
    ban_tracker[chat_id][admin_id]["bans"] = [
        ban_time for ban_time in ban_tracker[chat_id][admin_id]["bans"]
        if current_time - ban_time < BAN_TRACKING_TTL
    ]
    
    # Check if ban count exceeds threshold
    return len(ban_tracker[chat_id][admin_id]["bans"]) >= BAN_THRESHOLD

# Monitor chat member updates for ban actions
@app.on_chat_member_updated(group = 690)
@error
async def monitor_bans(client: Client, chat_member_updated: ChatMemberUpdated):
    # Skip if feature is not enabled for this chat
    chat_id = chat_member_updated.chat.id
    if not await is_antibanall_enabled(chat_id):
        return
    
    # Skip if the action is performed by the bot itself
    from_user = chat_member_updated.from_user
    if not from_user or from_user.id == config.BOT_ID:
        return
    
    # Check if this is a ban action
    old_status = None
    new_status = None
    
    if chat_member_updated.old_chat_member:
        old_status = chat_member_updated.old_chat_member.status
    
    if chat_member_updated.new_chat_member:
        new_status = chat_member_updated.new_chat_member.status
        target_user = chat_member_updated.new_chat_member.user
    else:
        return
    
    # If this is a ban action (user was not banned before and is now banned)
    if new_status == ChatMemberStatus.BANNED and old_status != ChatMemberStatus.BANNED:
        admin_id = from_user.id
        
        # Track this ban action
        ban_count = add_ban_action(chat_id, admin_id)
        
        # Check if admin is mass banning
        if ban_count >= BAN_THRESHOLD:
            # Try to demote the admin
            try:
                # Get chat member to check if bot can demote
                bot_member = await client.get_chat_member(chat_id, "me")
                
                # Check if bot has permission to demote
                if bot_member.privileges and bot_member.privileges.can_promote_members:
                    # Demote the admin
                    await client.promote_chat_member(
                        chat_id=chat_id,
                        user_id=admin_id,
                        privileges=None  # Remove all admin privileges
                    )
                    
                    # Notify the chat
                    admin_mention = f"<a href='tg://user?id={admin_id}'>{from_user.first_name}</a>"
                    await client.send_message(
                        chat_id,
                        f"⚠️ <b>𝖠𝗇𝗍𝗂𝖡𝖺𝗇𝖠𝗅𝗅 𝖯𝗋𝗈𝗍𝖾𝖼𝗍𝗂𝗈𝗇 𝖳𝗋𝗂𝗀𝗀𝖾𝗋𝖾𝖽</b> ⚠️\n\n"
                        f"{admin_mention} 𝗁𝖺𝗌 𝖻𝖾𝖾𝗇 𝖽𝖾𝗆𝗈𝗍𝖾𝖽 𝖿𝗈𝗋 𝖻𝖺𝗇𝗇𝗂𝗇𝗀 {ban_count} 𝗎𝗌𝖾𝗋𝗌 𝗂𝗇 𝗅𝖾𝗌𝗌 𝗍𝗁𝖺𝗇 {BAN_TRACKING_TTL} 𝗌𝖾𝖼𝗈𝗇𝖽𝗌.",
                        parse_mode=ParseMode.HTML
                    )
                    
                    # Log the action
                    log_message = await format_log(
                        action="AntiBanAll Protection Triggered",
                        chat=chat_member_updated.chat.title or str(chat_id),
                        admin=f"{admin_mention} ({admin_id})",
                        user=f"Banned {ban_count} users in {BAN_TRACKING_TTL} seconds"
                    )
                    await send_log(chat_id, log_message)
                else:
                    # Bot doesn't have permission to demote, alert all admins
                    admins = await client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS)
                    admin_mentions = " ".join([f"<a href='tg://user?id={admin.user.id}'>{admin.user.first_name}</a>" for admin in admins if not admin.user.is_bot])

                    await client.send_message(
                        chat_id,
                        f"⚠️ <b>𝖠𝗇𝗍𝗂𝖡𝖺𝗇𝖠𝗅𝗅 𝖠𝗅𝖾𝗋𝗍</b> ⚠️\n\n"
                        f"<a href='tg://user?id={admin_id}'>{from_user.first_name}</a> 𝗂𝗌 𝗆𝖺𝗌𝗌 𝖻𝖺𝗇𝗇𝗂𝗇𝗀 𝗎𝗌𝖾𝗋𝗌 ({ban_count} 𝖻𝖺𝗇𝗌 𝗂𝗇 {BAN_TRACKING_TTL} 𝗌𝖾𝖼𝗈𝗇𝖽𝗌).\n\n"
                        f"𝖨 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗉𝖾𝗋𝗆𝗂𝗌𝗌𝗂𝗈𝗇 𝗍𝗈 𝖽𝖾𝗆𝗈𝗍𝖾 𝗍𝗁𝗂𝗌 𝖺𝖽𝗆𝗂𝗇. 𝖢𝗁𝖺𝗍 𝗈𝗐𝗇𝖾𝗋𝗌, 𝗉𝗅𝖾𝖺𝗌𝖾 𝗍𝖺𝗄𝖾 𝖺𝖼𝗍𝗂𝗈𝗇!\n\n"
                        f"👮‍♂️ <b>𝖬𝖾𝗇𝗍𝗂𝗈𝗇𝗂𝗇𝗀 𝖠𝗅𝗅 𝖠𝖽𝗆𝗂𝗇𝗌:</b> {admin_mentions}",
                        parse_mode=ParseMode.HTML
                    )
                    
                    # Log the alert
                    log_message = await format_log(
                        action="AntiBanAll Alert (No Permission)",
                        chat=chat_member_updated.chat.title or str(chat_id),
                        admin=f"<a href='tg://user?id={admin_id}'>{from_user.first_name}</a> ({admin_id})",
                        user=f"Banned {ban_count} users in {BAN_TRACKING_TTL} seconds"
                    )
                    await send_log(chat_id, log_message)
            except Exception as e:
                # Log any errors
                log_message = await format_log(
                    action="AntiBanAll Error",
                    chat=chat_member_updated.chat.title or str(chat_id),
                    admin=f"Error: {str(e)}"
                )
                await send_log(chat_id, log_message)

# Module info
__module__ = "𝖠𝗇𝗍𝗂𝖡𝖺𝗇𝖠𝗅𝗅"
__help__ = """**✧ /𝖺𝗇𝗍𝗂𝖻𝖺𝗇𝖺𝗅𝗅** - 𝖳𝗈𝗀𝗀𝗅𝖾 𝖠𝗇𝗍𝗂𝖡𝖺𝗇𝖠𝗅𝗅 𝗉𝗋𝗈𝗍𝖾𝖼𝗍𝗂𝗈𝗇 𝗂𝗇 𝖺 𝖼𝗁𝖺𝗍.

𝖶𝗁𝖾𝗇 𝖾𝗇𝖺𝖻𝗅𝖾𝖽, 𝖨 𝗐𝗂𝗅𝗅 𝖽𝖾𝗆𝗈𝗍𝖾 𝖺𝗇𝗒 𝖺𝖽𝗆𝗂𝗇 𝗐𝗁𝗈 𝖻𝖺𝗇𝗌 𝗆𝗈𝗋𝖾 𝗍𝗁𝖺𝗇 5 𝗎𝗌𝖾𝗋𝗌 𝗂𝗇 10 𝗌𝖾𝖼𝗈𝗇𝖽𝗌.
𝖨𝖿 𝖨 𝖽𝗈𝗇'𝗍 𝗁𝖺𝗏𝖾 𝗉𝖾𝗋𝗆𝗂𝗌𝗌𝗂𝗈𝗇 𝗍𝗈 𝖽𝖾𝗆𝗈𝗍𝖾, 𝖨'𝗅𝗅 𝖺𝗅𝖾𝗋𝗍 𝖺𝗅𝗅 𝖺𝖽𝗆𝗂𝗇𝗌 𝗂𝗇 𝗍𝗁𝖾 𝖼𝗁𝖺𝗍.
""" 