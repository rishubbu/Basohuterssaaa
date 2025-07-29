from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid

from Yumeko import app , ANTIFLOOD_GROUP
from Yumeko.database.anti_flooddb import (
    get_antiflood_settings,
    set_flood_threshold,
    set_flood_timer,
    set_flood_action,
    set_delete_flood_messages,
    set_flood_action_duration,
    get_flood_action_duration
)
from Yumeko.helper.anti_flood_helper import flood_tracker
from Yumeko.helper.log_helper import format_log, send_log
from Yumeko.helper.user import MUTE
from Yumeko.decorator.chatadmin import can_change_info
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save
from config import config

import time
import threading
from datetime import datetime, timedelta
import re

# Constants
FLOOD_ACTIONS = ["mute", "kick", "ban", "tban", "tmute"]
MAX_FLOOD_THRESHOLD = 25  # Maximum allowed flood threshold
MAX_FLOOD_TIMER_COUNT = 50  # Maximum allowed flood timer count
MAX_FLOOD_TIMER_DURATION = 3600  # Maximum allowed flood timer duration in seconds (1 hour)
MAX_ACTION_DURATION = 31536000  # Maximum allowed action duration in seconds (1 year)

# Lock to prevent multiple actions on the same user
flood_action_locks = {}  # Dictionary to store locks for each (chat_id, user_id) pair
flood_lock = threading.Lock()  # Global lock for accessing the flood_action_locks dictionary

# Helper function to get readable time
def get_readable_time(seconds: int) -> str:
    """Convert seconds to a readable time format."""
    if seconds < 60:
        return f"{seconds} seconds"
    
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    time_parts = []
    if days > 0:
        time_parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        time_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        time_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds > 0:
        time_parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    
    return ", ".join(time_parts)

# Helper function to parse time arguments
def parse_time_arg(time_arg: str) -> int:
    """Parse time arguments like 1h, 2d, etc. into seconds."""
    if not time_arg:
        return 0
    
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    pattern = r"(\d+)([smhdw])"
    match = re.match(pattern, time_arg.lower())
    
    if not match:
        return 0
    
    value, unit = match.groups()
    return int(value) * time_units.get(unit, 0)

# Helper function to take action on a user
async def take_action_on_flood(client: Client, chat_id: int, user_id: int, action: str, duration_seconds: int = 0):
    """Take the specified action on a user who has triggered the flood protection."""
    try:
        # Get chat and user information for logging
        chat = await client.get_chat(chat_id)
        user = await client.get_users(user_id)
        
        action_taken = "No action"
        
        if action == "mute":
            await client.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=MUTE
            )
            action_taken = "Muted"
            
        elif action == "kick":
            await client.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )
            await client.unban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )
            action_taken = "Kicked"
            
        elif action == "ban":
            await client.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )
            action_taken = "Banned"
            
        elif action == "tban":
            until_date = datetime.now() + timedelta(seconds=duration_seconds)
            await client.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=until_date
            )
            action_taken = f"Temporarily banned for {get_readable_time(duration_seconds)}"
            
        elif action == "tmute":
            until_date = datetime.now() + timedelta(seconds=duration_seconds)
            await client.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=MUTE,
                until_date=until_date
            )
            action_taken = f"Temporarily muted for {get_readable_time(duration_seconds)}"
        
        # Log the action
        log_message = await format_log(
            action=f"Antiflood {action_taken}",
            chat=chat.title,
            user=f"{user.first_name} {user.last_name or ''} (@{user.username or 'N/A'}) [{user_id}]"
        )
        await send_log(chat_id, log_message)
        
        return action_taken
        
    except ChatAdminRequired:
        return "Failed: Bot needs admin rights"
    except UserAdminInvalid:
        return "Failed: User is an admin"
    except Exception as e:
        return f"Failed: {str(e)}"

# Command to set flood threshold
@app.on_message(filters.command("setflood", prefixes=config.COMMAND_PREFIXES) & filters.group)
@can_change_info
@error
@save
async def set_flood_command(client: Client, message: Message):
    chat_id = message.chat.id
    
    # Get current settings
    settings = await get_antiflood_settings(chat_id)
    
    # Ensure all required keys exist in settings
    settings.setdefault("flood_threshold", 0)
    settings.setdefault("flood_timer_count", 0)
    settings.setdefault("flood_timer_duration", 0)
    settings.setdefault("flood_action", "mute")
    settings.setdefault("delete_flood_messages", False)
    
    # Parse command arguments
    args = message.text.split()
    
    if len(args) == 1 or (len(args) == 2 and args[1].lower() == "info"):
        # Show current settings
        if settings["flood_threshold"] == 0:
            flood_mode = "Disabled"
        else:
            flood_mode = f"Enabled with threshold of {settings['flood_threshold']} messages"
        
        if settings["flood_timer_count"] > 0 and settings["flood_timer_duration"] > 0:
            flood_mode += f" or {settings['flood_timer_count']} messages in {get_readable_time(settings['flood_timer_duration'])}"
        
        action = settings["flood_action"].capitalize()
        if action in ["Tban", "Tmute"]:
            action_duration = await get_flood_action_duration(chat_id)
            action += f" for {get_readable_time(action_duration)}"
        
        delete_messages = "Yes" if settings["delete_flood_messages"] else "No"
        
        await message.reply_text(
            f"**Current Antiflood Settings:**\n\n"
            f"**Status:** {flood_mode}\n"
            f"**Action:** {action}\n"
            f"**Delete Messages:** {delete_messages}\n\n"
            f"**Commands:**\n"
            f"• `/setflood <number>` - Set flood threshold (0 to disable)\n"
            f"• `/setfloodmode <action>` - Set action (mute/kick/ban/tban/tmute)\n"
            f"• `/setfloodtime <duration>` - Set duration for tban/tmute\n"
            f"• `/setfloodtimer <count> <duration>` - Set timed flood detection\n"
            f"• `/delfloodmsg <on/off>` - Toggle deleting flood messages"
        )
        return
    
    # Set flood threshold
    try:
        threshold = int(args[1])
        if threshold < 0 or threshold > MAX_FLOOD_THRESHOLD:
            await message.reply_text(
                f"Invalid flood threshold. Please use a value between 0 and {MAX_FLOOD_THRESHOLD}.\n"
                f"Use 0 to disable antiflood."
            )
            return
        
        await set_flood_threshold(chat_id, threshold)
        
        if threshold == 0:
            await message.reply_text("Antiflood has been disabled.")
        else:
            await message.reply_text(
                f"Antiflood has been set to {threshold} messages.\n"
                f"Action: {settings['flood_action'].capitalize()}"
            )
            
    except ValueError:
        await message.reply_text(
            "Invalid format. Please use `/setflood <number>`.\n"
            "Use 0 to disable antiflood."
        )

# Command to set flood action mode
@app.on_message(filters.command("setfloodmode", prefixes=config.COMMAND_PREFIXES) & filters.group)
@can_change_info
@error
@save
async def set_flood_mode_command(client: Client, message: Message):
    chat_id = message.chat.id
    
    # Get current settings
    settings = await get_antiflood_settings(chat_id)
    
    # Ensure all required keys exist in settings
    settings.setdefault("flood_threshold", 0)
    settings.setdefault("flood_timer_count", 0)
    settings.setdefault("flood_timer_duration", 0)
    settings.setdefault("flood_action", "mute")
    settings.setdefault("delete_flood_messages", False)
    
    # Parse command arguments
    args = message.text.split()
    
    if len(args) < 2:
        await message.reply_text(
            "Please specify an action.\n"
            "Available actions: mute, kick, ban, tban, tmute\n\n"
            "Example: `/setfloodmode ban`"
        )
        return
    
    action = args[1].lower()
    
    if action not in FLOOD_ACTIONS:
        await message.reply_text(
            "Invalid action. Available actions: mute, kick, ban, tban, tmute"
        )
        return
    
    await set_flood_action(chat_id, action)
    
    # If action is tban or tmute, check for duration
    if action in ["tban", "tmute"]:
        duration_seconds = 86400  # Default: 1 day
        
        if len(args) >= 3:
            try:
                duration_arg = args[2]
                duration_seconds = parse_time_arg(duration_arg)
                if duration_seconds <= 0 or duration_seconds > MAX_ACTION_DURATION:
                    await message.reply_text(
                        f"Invalid duration. Please use a value between 1 second and {get_readable_time(MAX_ACTION_DURATION)}."
                    )
                    return
                
                await set_flood_action_duration(chat_id, duration_seconds)
            except ValueError:
                await message.reply_text("Invalid time format. Use formats like 1h, 2d, etc.")
                return
        
        await message.reply_text(
            f"Antiflood action has been set to {action} for {get_readable_time(duration_seconds)}."
        )
    else:
        await message.reply_text(f"Antiflood action has been set to {action}.")

# Command to set flood action duration
@app.on_message(filters.command("setfloodtime", prefixes=config.COMMAND_PREFIXES) & filters.group)
@can_change_info
@error
@save
async def set_flood_time_command(client: Client, message: Message):
    chat_id = message.chat.id
    
    # Get current settings
    settings = await get_antiflood_settings(chat_id)
    
    # Ensure all required keys exist in settings
    settings.setdefault("flood_threshold", 0)
    settings.setdefault("flood_timer_count", 0)
    settings.setdefault("flood_timer_duration", 0)
    settings.setdefault("flood_action", "mute")
    settings.setdefault("delete_flood_messages", False)
    
    # Parse command arguments
    args = message.text.split()
    
    if len(args) < 2:
        await message.reply_text(
            "Please specify a duration.\n"
            "Example: `/setfloodtime 1d` (1 day)\n"
            "Formats: s (seconds), m (minutes), h (hours), d (days), w (weeks)"
        )
        return
    
    if settings["flood_action"] not in ["tban", "tmute"]:
        await message.reply_text(
            f"Current action is set to {settings['flood_action']}. Duration only applies to tban or tmute.\n"
            f"Change the action first with `/setfloodmode tban` or `/setfloodmode tmute`."
        )
        return
    
    try:
        duration_arg = args[1]
        duration_seconds = parse_time_arg(duration_arg)
        
        if duration_seconds <= 0 or duration_seconds > MAX_ACTION_DURATION:
            await message.reply_text(
                f"Invalid duration. Please use a value between 1 second and {get_readable_time(MAX_ACTION_DURATION)}."
            )
            return
        
        await set_flood_action_duration(chat_id, duration_seconds)
        
        await message.reply_text(
            f"Antiflood {settings['flood_action']} duration has been set to {get_readable_time(duration_seconds)}."
        )
        
    except ValueError:
        await message.reply_text("Invalid time format. Use formats like 1h, 2d, etc.")

# Command to set timed flood detection
@app.on_message(filters.command("setfloodtimer", prefixes=config.COMMAND_PREFIXES) & filters.group)
@can_change_info
@error
@save
async def set_flood_timer_command(client: Client, message: Message):
    chat_id = message.chat.id
    
    # Get current settings
    settings = await get_antiflood_settings(chat_id)
    
    # Ensure all required keys exist in settings
    settings.setdefault("flood_threshold", 0)
    settings.setdefault("flood_timer_count", 0)
    settings.setdefault("flood_timer_duration", 0)
    settings.setdefault("flood_action", "mute")
    settings.setdefault("delete_flood_messages", False)
    
    # Parse command arguments
    args = message.text.split()
    
    if len(args) < 3:
        await message.reply_text(
            "Please specify count and duration.\n"
            "Example: `/setfloodtimer 10 30s` (10 messages in 30 seconds)\n"
            "Use 0 0 to disable timed flood detection."
        )
        return
    
    try:
        count = int(args[1])
        duration_arg = args[2]
        
        if count == 0:
            # Disable timed flood detection
            await set_flood_timer(chat_id, 0, 0)
            await message.reply_text("Timed flood detection has been disabled.")
            return
        
        if count < 0 or count > MAX_FLOOD_TIMER_COUNT:
            await message.reply_text(
                f"Invalid count. Please use a value between 1 and {MAX_FLOOD_TIMER_COUNT}."
            )
            return
        
        duration_seconds = parse_time_arg(duration_arg)
        
        if duration_seconds <= 0 or duration_seconds > MAX_FLOOD_TIMER_DURATION:
            await message.reply_text(
                f"Invalid duration. Please use a value between 1 second and {get_readable_time(MAX_FLOOD_TIMER_DURATION)}."
            )
            return
        
        await set_flood_timer(chat_id, count, duration_seconds)
        
        await message.reply_text(
            f"Timed flood detection has been set to {count} messages in {get_readable_time(duration_seconds)}."
        )
        
    except ValueError:
        await message.reply_text(
            "Invalid format. Please use `/setfloodtimer <count> <duration>`.\n"
            "Example: `/setfloodtimer 10 30s` (10 messages in 30 seconds)"
        )

# Command to toggle deleting flood messages
@app.on_message(filters.command("delfloodmsg", prefixes=config.COMMAND_PREFIXES) & filters.group)
@can_change_info
@error
@save
async def toggle_delete_flood_messages_command(client: Client, message: Message):
    chat_id = message.chat.id
    
    # Get current settings
    settings = await get_antiflood_settings(chat_id)
    
    # Ensure all required keys exist in settings
    settings.setdefault("flood_threshold", 0)
    settings.setdefault("flood_timer_count", 0)
    settings.setdefault("flood_timer_duration", 0)
    settings.setdefault("flood_action", "mute")
    settings.setdefault("delete_flood_messages", False)
    
    # Parse command arguments
    args = message.text.split()
    
    if len(args) < 2:
        await message.reply_text(
            "Please specify on or off.\n"
            "Example: `/delfloodmsg on`"
        )
        return
    
    option = args[1].lower()
    
    if option not in ["on", "off", "yes", "no", "true", "false", "1", "0"]:
        await message.reply_text("Invalid option. Please use on or off.")
        return
    
    delete_messages = option in ["on", "yes", "true", "1"]
    
    await set_delete_flood_messages(chat_id, delete_messages)
    
    if delete_messages:
        await message.reply_text("Flood messages will now be deleted.")
    else:
        await message.reply_text("Flood messages will not be deleted.")

# Helper function to get or create a lock for a specific chat-user pair
def get_action_lock(chat_id: int, user_id: int) -> threading.Lock:
    """Get or create a lock for a specific chat-user pair."""
    key = (chat_id, user_id)
    with flood_lock:
        if key not in flood_action_locks:
            flood_action_locks[key] = threading.Lock()
        return flood_action_locks[key]

# Message handler for flood detection
@app.on_message(filters.group & ~filters.service & ~filters.me & ~filters.bot & ~filters.via_bot, group=ANTIFLOOD_GROUP)
@error
@save
async def check_flood(client: Client, message: Message):
    # Skip if no user or chat
    if not message.from_user or not message.chat:
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Get antiflood settings
    settings = await get_antiflood_settings(chat_id)
    
    # Ensure all required keys exist in settings
    settings.setdefault("flood_threshold", 0)
    settings.setdefault("flood_timer_count", 0)
    settings.setdefault("flood_timer_duration", 0)
    settings.setdefault("flood_action", "mute")
    settings.setdefault("delete_flood_messages", False)
    
    # Skip if antiflood is disabled
    if settings["flood_threshold"] == 0 and (settings["flood_timer_count"] == 0 or settings["flood_timer_duration"] == 0):
        return
    
    # Skip for admins
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
    except Exception:
        pass  # Continue if we can't get member info
    
    # Initialize user tracker for this chat if it doesn't exist
    if (chat_id, user_id) not in flood_tracker:
        flood_tracker[(chat_id, user_id)] = {"count": 0, "timestamps": [], "messages": []}
    
    # Get user tracker for this chat
    chat_tracker = flood_tracker[(chat_id, user_id)]
    
    # Update message count and timestamps
    current_time = time.time()
    chat_tracker["count"] += 1
    chat_tracker["timestamps"].append(current_time)
    chat_tracker["messages"].append(message)
    
    # Get the lock for this chat-user pair
    action_lock = get_action_lock(chat_id, user_id)
    
    # Try to acquire the lock, but don't block if it's already locked
    # This prevents multiple actions being taken on the same user simultaneously
    if not action_lock.acquire(blocking=False):
        # Lock is already held, which means another instance is already handling this user's flood
        return
    
    try:
        # Check for regular flood threshold
        if settings["flood_threshold"] > 0 and chat_tracker["count"] >= settings["flood_threshold"]:
            # User has exceeded the flood threshold
            action = settings["flood_action"]
            duration_seconds = await get_flood_action_duration(chat_id) if action in ["tban", "tmute"] else 0
            
            # Take action on the user
            action_taken = await take_action_on_flood(client, chat_id, user_id, action, duration_seconds)
            
            # Notify the chat
            notification = (
                f"**Flood detected!**\n"
                f"User: {message.from_user.mention} has been flooding the chat.\n"
                f"Action taken: {action_taken}"
            )
            
            await message.reply_text(notification)
            
            # Delete flood messages if enabled
            if settings["delete_flood_messages"]:
                for msg in chat_tracker["messages"]:
                    try:
                        await msg.delete()
                    except Exception:
                        pass
            
            # Reset the tracker
            flood_tracker[(chat_id, user_id)] = {"count": 0, "timestamps": [], "messages": []}
            return
        
        # Check for timed flood threshold
        if settings["flood_timer_count"] > 0 and settings["flood_timer_duration"] > 0:
            # Filter timestamps within the time window
            time_window = current_time - settings["flood_timer_duration"]
            recent_timestamps = [ts for ts in chat_tracker["timestamps"] if ts > time_window]
            
            # Update the tracker with only recent timestamps
            chat_tracker["timestamps"] = recent_timestamps
            
            # Check if the user has exceeded the timed flood threshold
            if len(recent_timestamps) >= settings["flood_timer_count"]:
                # User has exceeded the timed flood threshold
                action = settings["flood_action"]
                duration_seconds = await get_flood_action_duration(chat_id) if action in ["tban", "tmute"] else 0
                
                # Take action on the user
                action_taken = await take_action_on_flood(client, chat_id, user_id, action, duration_seconds)
                
                # Notify the chat
                notification = (
                    f"**Timed flood detected!**\n"
                    f"User: {message.from_user.mention} sent {len(recent_timestamps)} messages in "
                    f"{get_readable_time(settings['flood_timer_duration'])}.\n"
                    f"Action taken: {action_taken}"
                )
                
                await message.reply_text(notification)
                
                # Delete flood messages if enabled
                if settings["delete_flood_messages"]:
                    for msg in chat_tracker["messages"]:
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                
                # Reset the tracker
                flood_tracker[(chat_id, user_id)] = {"count": 0, "timestamps": [], "messages": []}
                return
        
        # Clean up old messages from tracker to prevent memory issues
        if len(chat_tracker["messages"]) > MAX_FLOOD_THRESHOLD:
            chat_tracker["messages"] = chat_tracker["messages"][-MAX_FLOOD_THRESHOLD:]
    
    finally:
        # Always release the lock when done
        action_lock.release()

# Periodic cleanup of flood tracker and locks
async def cleanup_flood_tracker():
    try:
        current_time = time.time()
        keys_to_remove = []
        
        for key, data in flood_tracker.items():
            # Remove entries older than 1 hour
            if not data["timestamps"] or current_time - max(data["timestamps"]) > 3600:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del flood_tracker[key]
            
            # Also clean up the corresponding lock if it exists
            with flood_lock:
                if key in flood_action_locks:
                    del flood_action_locks[key]
            
        if keys_to_remove:
            print(f"Cleaned up {len(keys_to_remove)} flood tracker entries")
            
    except Exception as e:
        print(f"Error in cleanup_flood_tracker: {e}")

__module__ = "𝖠𝗇𝗍𝗂𝖿𝗅𝗈𝗈𝖽"

__help__ = """
**𝖠𝗇𝗍𝗂𝖿𝗅𝗈𝗈𝖽**

𝖳𝗁𝗂𝗌 𝗆𝗈𝖽𝗎𝗅𝖾 𝗁𝖾𝗅𝗉𝗌 𝗉𝗋𝗈𝗍𝖾𝖼𝗍 𝗒𝗈𝗎𝗋 𝗀𝗋𝗈𝗎𝗉 𝖿𝗋𝗈𝗆 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝖿𝗅𝗈𝗈𝖽𝗂𝗇𝗀 𝖻𝗒 𝖺𝗎𝗍𝗈𝗆𝖺𝗍𝗂𝖼𝖺𝗅𝗅𝗒 𝗍𝖺𝗄𝗂𝗇𝗀 𝖺𝖼𝗍𝗂𝗈𝗇 𝖺𝗀𝖺𝗂𝗇𝗌𝗍 𝗎𝗌𝖾𝗋𝗌 𝗐𝗁𝗈 𝗌𝖾𝗇𝖽 𝗍𝗈𝗈 𝗆𝖺𝗇𝗒 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝗂𝗇 𝖺 𝗋𝗈𝗐.
  
**𝖠𝖽𝗆𝗂𝗇 𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌:**
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽 <𝗇𝗎𝗆𝖻𝖾𝗋>` - 𝖲𝖾𝗍 𝗍𝗁𝖾 𝗇𝗎𝗆𝖻𝖾𝗋 𝗈𝖿 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝖺𝖿𝗍𝖾𝗋 𝗐𝗁𝗂𝖼𝗁 𝗍𝗈 𝗍𝖺𝗄𝖾 𝖺𝖼𝗍𝗂𝗈𝗇 (𝟢 𝗍𝗈 𝖽𝗂𝗌𝖺𝖻𝗅𝖾)
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽𝗆𝗈𝖽𝖾 <𝖺𝖼𝗍𝗂𝗈𝗇>` - 𝖲𝖾𝗍 𝗍𝗁𝖾 𝖺𝖼𝗍𝗂𝗈𝗇 𝗍𝗈 𝗍𝖺𝗄𝖾 (𝗆𝗎𝗍𝖾/𝗄𝗂𝖼𝗄/𝖻𝖺𝗇/𝗍𝖻𝖺𝗇/𝗍𝗆𝗎𝗍𝖾)
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽𝗍𝗂𝗆𝖾 <𝖽𝗎𝗋𝖺𝗍𝗂𝗈𝗇>` - 𝖲𝖾𝗍 𝗍𝗁𝖾 𝖽𝗎𝗋𝖺𝗍𝗂𝗈𝗇 𝖿𝗈𝗋 𝗍𝖻𝖺𝗇/𝗍𝗆𝗎𝗍𝖾 (𝖾.𝗀., 𝟣𝗁, 𝟤𝖽)
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽𝗍𝗂𝗆𝖾𝗋 <𝖼𝗈𝗎𝗇𝗍> <𝖽𝗎𝗋𝖺𝗍𝗂𝗈𝗇>` - 𝖲𝖾𝗍 𝗍𝗂𝗆𝖾𝖽 𝖿𝗅𝗈𝗈𝖽 𝖽𝖾𝗍𝖾𝖼𝗍𝗂𝗈𝗇 (𝖾.𝗀., 𝟣𝟢 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝗂𝗇 𝟥𝟢𝗌)
• `/𝖽𝖾𝗅𝖿𝗅𝗈𝗈𝖽𝗆𝗌𝗀 <𝗈𝗇/𝗈𝖿𝖿>` - 𝖳𝗈𝗀𝗀𝗅𝖾 𝗐𝗁𝖾𝗍𝗁𝖾𝗋 𝗍𝗈 𝖽𝖾𝗅𝖾𝗍𝖾 𝗍𝗁𝖾 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝗍𝗁𝖺𝗍 𝗍𝗋𝗂𝗀𝗀𝖾𝗋𝖾𝖽 𝗍𝗁𝖾 𝖿𝗅𝗈𝗈𝖽
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽 𝗂𝗇𝖿𝗈` - 𝖲𝗁𝗈𝗐 𝖼𝗎𝗋𝗋𝖾𝗇𝗍 𝖺𝗇𝗍𝗂𝖿𝗅𝗈𝗈𝖽 𝗌𝖾𝗍𝗍𝗂𝗇𝗀𝗌

**𝖤𝗑𝖺𝗆𝗉𝗅𝖾𝗌:**
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽 𝟧` - 𝖳𝖺𝗄𝖾 𝖺𝖼𝗍𝗂𝗈𝗇 𝖺𝖿𝗍𝖾𝗋 𝟧 𝖼𝗈𝗇𝗌𝖾𝖼𝗎𝗍𝗂𝗏𝖾 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽𝗆𝗈𝖽𝖾 𝖻𝖺𝗇` - 𝖡𝖺𝗇 𝗎𝗌𝖾𝗋𝗌 𝗐𝗁𝗈 𝖿𝗅𝗈𝗈𝖽
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽𝗆𝗈𝖽𝖾 𝗍𝗆𝗎𝗍𝖾 𝟤𝗁` - 𝖳𝖾𝗆𝗉𝗈𝗋𝖺𝗋𝗂𝗅𝗒 𝗆𝗎𝗍𝖾 𝗎𝗌𝖾𝗋𝗌 𝖿𝗈𝗋 𝟤 𝗁𝗈𝗎𝗋𝗌
• `/𝗌𝖾𝗍𝖿𝗅𝗈𝗈𝖽𝗍𝗂𝗆𝖾𝗋 𝟣𝟢 𝟥𝟢𝗌` - 𝖳𝖺𝗄𝖾 𝖺𝖼𝗍𝗂𝗈𝗇 𝗂𝖿 𝖺 𝗎𝗌𝖾𝗋 𝗌𝖾𝗇𝖽𝗌 𝟣𝟢+ 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝗂𝗇 𝟥𝟢 𝗌𝖾𝖼𝗈𝗇𝖽𝗌

**𝖭𝗈𝗍𝖾:** 𝖠𝖽𝗆𝗂𝗇𝗌 𝖺𝗋𝖾 𝖾𝗑𝖾𝗆𝗉𝗍 𝖿𝗋𝗈𝗆 𝖿𝗅𝗈𝗈𝖽 𝖽𝖾𝗍𝖾𝖼𝗍𝗂𝗈𝗇.
"""
