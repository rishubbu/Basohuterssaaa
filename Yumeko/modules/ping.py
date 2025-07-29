import time
import psutil
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from Yumeko import app, start_time
from config import config
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save


@app.on_message(filters.command("ping", config.COMMAND_PREFIXES))
@error
@save
async def ping_command(_, message: Message):
    """Check the bot's response time and system stats"""
    
    # Record start time
    start = time.time()
    
    # Send a message and measure the time it takes
    ping_msg = await message.reply_text("Pinging...")
    
    # Calculate ping time
    end = time.time()
    ping_time = round((end - start) * 1000, 3)
    
    # Get uptime
    uptime = datetime.now() - datetime.fromtimestamp(start_time)
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    # Get system stats
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    # Format the response message
    response = (
        f"**PONG!** `{ping_time}ms`\n\n"
        f"**Uptime:** `{uptime_str}`\n"
        f"**CPU Usage:** `{cpu_usage}%`\n"
        f"**RAM Usage:** `{ram_usage}%`\n"
        f"**Disk Usage:** `{disk_usage}%`\n"
        f"**Version:** `{config.BOT_VERSION}`"
    )
    
    await ping_msg.edit_text(response) 