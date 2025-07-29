from pyrogram import Client, filters
from pyrogram.types import Message
import re
import os
import asyncio
from urllib.parse import urlparse
import logging

from Yumeko import app
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save
from config import config

# Constants
MAX_URL_LENGTH = 500  # Maximum URL length to prevent abuse
SCREENSHOT_TIMEOUT = 30  # Timeout in seconds for taking screenshots

# Helper function to validate and format URLs
def format_url(url: str) -> str:
    """
    Format and validate a URL.
    
    Args:
        url: The URL to format
        
    Returns:
        Properly formatted URL
    """
    # Check if URL is too long
    if len(url) > MAX_URL_LENGTH:
        raise ValueError("URL is too long")
    
    # Add https:// if no protocol specified
    if not re.match(r'^https?://', url, re.IGNORECASE):
        url = f"https://{url}"
    
    # Validate URL format
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
    except Exception:
        raise ValueError("Invalid URL format")
    
    return url

# Function to take screenshot using Playwright
async def take_screenshot(url, output_path):
    """
    Take a screenshot of a website using Playwright.
    
    Args:
        url: The URL to take a screenshot of
        output_path: The path to save the screenshot to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import Playwright modules here to avoid loading them if not needed
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Launch a browser (chromium, firefox, or webkit)
            browser = await p.chromium.launch(headless=True)
            
            # Create a new page
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            
            # Navigate to the URL with a timeout
            await page.goto(url, timeout=SCREENSHOT_TIMEOUT * 1000, wait_until="networkidle")
            
            # Wait a bit for any remaining JavaScript to execute
            await asyncio.sleep(1)
            
            # Take screenshot
            await page.screenshot(path=output_path, full_page=False)
            
            # Close the browser
            await browser.close()
            
            return True
    except Exception as e:
        logging.error(f"Error taking screenshot with Playwright: {str(e)}")
        return False

# Screenshot command
@app.on_message(filters.command(["ss", "webss", "screenshot"], prefixes=config.COMMAND_PREFIXES))
@error
@save
async def screenshot_command(client: Client, message: Message):
    """
    Take a screenshot of a website.
    
    Command:
        /ss <url>
        /webss <url>
        /screenshot <url>
    """
    # Check if URL is provided
    if len(message.command) < 2:
        await message.reply_text(
            "Please provide a URL to take a screenshot of.\n\n"
            "**Usage:** `/ss example.com`"
        )
        return
    
    # Get URL from command
    url = message.command[1]
    
    # Send processing message
    processing_msg = await message.reply_text("Processing screenshot request...")
    
    try:
        # Format URL
        formatted_url = format_url(url)
        
        # Create a unique filename for the screenshot
        screenshot_path = f"screenshot_{message.from_user.id}_{int(message.date.timestamp())}.png"
        
        # Take screenshot
        success = await take_screenshot(formatted_url, screenshot_path)
        
        # If screenshot fails, notify the user
        if not success:
            await processing_msg.edit_text("Failed to take screenshot. Please try again later.")
            return
        
        # Check if the screenshot file exists and has content
        if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
            await processing_msg.edit_text("Failed to generate screenshot. Please try again later.")
            return
        
        # Send screenshot
        await message.reply_photo(
            screenshot_path,
            caption=f"📸 Screenshot of [{urlparse(formatted_url).netloc}]({formatted_url})"
        )
        
        # Delete temporary file
        os.remove(screenshot_path)
        
        # Delete processing message
        await processing_msg.delete()
    
    except ValueError as e:
        await processing_msg.edit_text(f"Error: {str(e)}")
    except Exception as e:
        await processing_msg.edit_text(f"An error occurred: {str(e)}")

__module__ = "𝖶𝖾𝖻 𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍"

__help__ = """
**𝖶𝖾𝖻 𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍**

𝖳𝖺𝗄𝖾 𝗌𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍𝗌 𝗈𝖿 𝗐𝖾𝖻𝗌𝗂𝗍𝖾𝗌 𝖽𝗂𝗋𝖾𝖼𝗍𝗅𝗒 𝖿𝗋𝗈𝗆 𝖳𝖾𝗅𝖾𝗀𝗋𝖺𝗆.
 
**𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌:**
• `/𝗌𝗌 <𝗎𝗋𝗅>` - 𝖳𝖺𝗄𝖾 𝖺 𝗌𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍 𝗈𝖿 𝗍𝗁𝖾 𝗌𝗉𝖾𝖼𝗂𝖿𝗂𝖾𝖽 𝗐𝖾𝖻𝗌𝗂𝗍𝖾
• `/𝗐𝖾𝖻𝗌𝗌 <𝗎𝗋𝗅>` - 𝖠𝗅𝗂𝖺𝗌 𝖿𝗈𝗋 /𝗌𝗌
• `/𝗌𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍 <𝗎𝗋𝗅>` - 𝖠𝗅𝗂𝖺𝗌 𝖿𝗈𝗋 /𝗌𝗌

**𝖤𝗑𝖺𝗆𝗉𝗅𝖾𝗌:**
• `/𝗌𝗌 𝗀𝗈𝗈𝗀𝗅𝖾.𝖼𝗈𝗆`
• `/𝗌𝗌 𝗁𝗍𝗍𝗉𝗌://𝗀𝗂𝗍𝗁𝗎𝖻.𝖼𝗈𝗆`

**𝖭𝗈𝗍𝖾:** 
- 𝖳𝗁𝖾 𝖴𝖱𝖫 𝗐𝗂𝗅𝗅 𝖻𝖾 𝖺𝗎𝗍𝗈𝗆𝖺𝗍𝗂𝖼𝖺𝗅𝗅𝗒 𝖿𝗈𝗋𝗆𝖺𝗍𝗍𝖾𝖽 𝗂𝖿 𝗒𝗈𝗎 𝖽𝗈𝗇'𝗍 𝗂𝗇𝖼𝗅𝗎𝖽𝖾 𝗍𝗁𝖾 𝗉𝗋𝗈𝗍𝗈𝖼𝗈𝗅 (𝗁𝗍𝗍𝗉:// 𝗈𝗋 𝗁𝗍𝗍𝗉𝗌://)
- 𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍𝗌 𝖺𝗋𝖾 𝗍𝖺𝗄𝖾𝗇 𝖺𝗍 𝟣𝟤𝟪𝟢𝗑𝟪𝟢𝟢 𝗋𝖾𝗌𝗈𝗅𝗎𝗍𝗂𝗈𝗇
- 𝖳𝗁𝗂𝗌 𝖿𝖾𝖺𝗍𝗎𝗋𝖾 𝗋𝖾𝗊𝗎𝗂𝗋𝖾𝗌 𝖯𝗅𝖺𝗒𝗐𝗋𝗂𝗀𝗁𝗍 𝗍𝗈 𝖻𝖾 𝗂𝗇𝗌𝗍𝖺𝗅𝗅𝖾𝖽 𝗈𝗇 𝗍𝗁𝖾 𝗌𝖾𝗋𝗏𝖾𝗋
""" 