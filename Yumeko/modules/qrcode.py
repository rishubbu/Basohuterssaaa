import qrcode
from io import BytesIO
from pyrogram import filters
from pyrogram.types import Message
from Yumeko import app
from config import config
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save


@app.on_message(filters.command("qrcode", config.COMMAND_PREFIXES))
@error
@save
async def generate_qrcode(_, message: Message):
    """Generate a QR code from text or URL"""
    
    # Check if there's text after the command
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(
            "Please provide text or a URL to generate a QR code, or reply to a message.\n\n"
            "**Usage:** `/qrcode [text or URL]`"
        )
        return
    
    # Get the text to encode
    if len(message.command) >= 2:
        text = message.text.split(None, 1)[1]
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    else:
        await message.reply_text("Please provide text or a URL to generate a QR code.")
        return
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to BytesIO
    bio = BytesIO()
    bio.name = "qrcode.png"
    img.save(bio, "PNG")
    bio.seek(0)
    
    # Send the QR code
    await message.reply_photo(
        bio,
        caption=f"**QR Code for:**\n`{text[:50]}{'...' if len(text) > 50 else ''}`"
    ) 

__module__ = "𝖰𝖱 𝖢𝗈𝖽𝖾"
__help__ = """
𝖦𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖰𝖱 𝖼𝗈𝖽𝖾𝗌 𝖿𝗋𝗈𝗆 𝗍𝖾𝗑𝗍 𝗈𝗋 𝖴𝖱𝖫𝗌.
 
**𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌:**
- /𝗊𝗋𝖼𝗈𝖽𝖾 [𝗍𝖾𝗑𝗍/𝗎𝗋𝗅]: 𝖦𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝖰𝖱 𝖼𝗈𝖽𝖾
"""
