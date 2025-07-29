import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os
from Yumeko import app
from pyrogram.types import InlineKeyboardButton , InlineKeyboardMarkup
from config import config 

class Upload:
    def __init__(self):
        self.catbox_url = "https://catbox.moe/user/api.php"
        self.pastebin_url = "https://pastebin.com/api/api_post.php"
        self.pastebin_api_key = config.PASTEBIN_API  # Replace with your actual API key

    def upload_to_catbox(self, file_path):
        with open(file_path, 'rb') as file:
            data = {'reqtype': 'fileupload'}
            files = {'fileToUpload': file}
            response = requests.post(self.catbox_url, data=data, files=files)
        
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to upload file. Status code: {response.status_code}"

    def upload_text_to_pastebin(self, title, content):
        data = {
            'api_dev_key': self.pastebin_api_key,
            'api_option': 'paste',
            'api_paste_code': content,
            'api_paste_name': title,
            'api_paste_private': 1,  # Private paste
        }
        response = requests.post(self.pastebin_url, data=data)
        
        if response.status_code == 200 and "http" in response.text:
            return response.text
        else:
            raise Exception(f"Failed to upload to Pastebin: {response.text}")

uploader = Upload()

# /tgm command: Reply to a media file and upload to catbox
@app.on_message(filters.command("tgm" , prefixes=config.COMMAND_PREFIXES) & filters.reply)
async def upload_to_catbox(client: Client, message: Message):
    reply_msg = message.reply_to_message
    
    # Check for all supported media types
    supported_media = (
        reply_msg.photo or reply_msg.video or reply_msg.audio or 
        reply_msg.document or reply_msg.animation or reply_msg.sticker or
        reply_msg.voice or reply_msg.video_note
    )
    
    if not supported_media:
        await message.reply("𝖯𝗅𝖾𝖺𝗌𝖾 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗌𝗎𝗉𝗉𝗈𝗋𝗍𝖾𝖽 𝗆𝖾𝖽𝗂𝖺 (𝗉𝗁𝗈𝗍𝗈, 𝗏𝗂𝖽𝖾𝗈, 𝖺𝗎𝖽𝗂𝗈, 𝖽𝗈𝖼𝗎𝗆𝖾𝗇𝗍, 𝖺𝗇𝗂𝗆𝖺𝗍𝗂𝗈𝗇, 𝗌𝗍𝗂𝖼𝗄𝖾𝗋, 𝗏𝗈𝗂𝖼𝖾, 𝗏𝗂𝖽𝖾𝗈 𝗇𝗈𝗍𝖾).")
        return

    # Get media type for status message
    media_type = "file"
    if reply_msg.photo:
        media_type = "photo"
    elif reply_msg.video:
        media_type = "video"
    elif reply_msg.audio:
        media_type = "audio"
    elif reply_msg.animation:
        media_type = "animation/GIF"
    elif reply_msg.sticker:
        media_type = "sticker"
    elif reply_msg.voice:
        media_type = "voice message"
    elif reply_msg.video_note:
        media_type = "video note"
    elif reply_msg.document:
        media_type = "document"

    a = await message.reply_text(f"𝖣𝗈𝗐𝗇𝗅𝗈𝖺𝖽𝗂𝗇𝗀 𝗍𝗁𝖾 {media_type}...")

    try:
        file_path = await reply_msg.download()
        
        await a.edit_text(f"𝖳𝗋𝗒𝗂𝗇𝗀 𝗍𝗈 𝗎𝗉𝗅𝗈𝖺𝖽 {media_type} 𝗍𝗈 𝗍𝗁𝖾 𝖠𝖯𝖨...")
        catbox_link = uploader.upload_to_catbox(file_path)
        link = f"https://telegram.me/share/url?url={catbox_link}"
        
        share_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔗 𝖲𝗁𝖺𝗋𝖾 𝖫𝗂𝗇𝗄", url=link)]]
        )
        await a.edit_text(f"**{media_type.capitalize()} 𝗎𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝗌𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒**: [𝖫𝗂𝗇𝗄]({catbox_link})", disable_web_page_preview=True, reply_markup=share_button)
    except Exception as e:
        await message.reply(f"𝖥𝖺𝗂𝗅𝖾𝖽 𝗍𝗈 𝗎𝗉𝗅𝗈𝖺𝖽 {media_type}: {str(e)}")
    finally:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

@app.on_message(filters.command("tgt" , prefixes=config.COMMAND_PREFIXES))
async def upload_to_telegraph(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.text:
        content = message.reply_to_message.text
    elif len(message.command) > 1:
        content = message.text.split(" ", 1)[1]
    else:
        await message.reply("𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗍𝖾𝗑𝗍 𝗍𝗈 𝗎𝗉𝗅𝗈𝖺𝖽 𝗂𝗍 𝗍𝗈 𝖯𝖺𝗌𝗍𝖾𝖻𝗂𝗇.")
        return

    try:
        a = await message.reply_text("𝖳𝗋𝗒𝗂𝗇𝗀 𝖳𝗈 𝖴𝗉𝗅𝗈𝖺𝖽 𝖳𝗈 𝖳𝗁𝖾 𝖠𝖯𝖨...")
        title = f"Uploaded by {message.from_user.first_name}"
        pastebin_link = uploader.upload_text_to_pastebin(title, content)
        link = f"https://telegram.me/share/url?url={pastebin_link}"
        
        share_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔗 𝖲𝗁𝖺𝗋𝖾 𝖫𝗂𝗇𝗄", url=link)]]
        )
        await a.edit_text(f"**𝖳𝖾𝗑𝗍 𝗎𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝗌𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅𝗅𝗒 **: [𝖫𝗂𝗇𝗄]({pastebin_link})", disable_web_page_preview=True , reply_markup=share_button)
    except Exception as e:
        await message.reply(f"𝖥𝖺𝗂𝗅𝖾𝖽 𝗍𝗈 𝗎𝗉𝗅𝗈𝖺𝖽 𝗍𝖾𝗑𝗍 : {str(e)}")
        

__module__ = "𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝗋"


__help__ = """**𝖴𝗉𝗅𝗈𝖺𝖽𝖾𝗋 𝖡𝗈𝗍 𝖥𝖾𝖺𝗍𝗎𝗋𝖾𝗌:**

- **𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌:**

 ✧ `/𝗍𝗀𝗆` : 𝖱𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺𝗇𝗒 𝗆𝖾𝖽𝗂𝖺 (𝗉𝗁𝗈𝗍𝗈, 𝗏𝗂𝖽𝖾𝗈, 𝖺𝗎𝖽𝗂𝗈, 𝖽𝗈𝖼𝗎𝗆𝖾𝗇𝗍, 𝖺𝗇𝗂𝗆𝖺𝗍𝗂𝗈𝗇, 𝗌𝗍𝗂𝖼𝗄𝖾𝗋, 𝗏𝗈𝗂𝖼𝖾, 𝗏𝗂𝖽𝖾𝗈 𝗇𝗈𝗍𝖾), 𝖺𝗇𝖽 𝗍𝗁𝖾 𝖻𝗈𝗍 𝗐𝗂𝗅𝗅 𝗎𝗉𝗅𝗈𝖺𝖽 𝗂𝗍 𝗍𝗈 𝖢𝖺𝗍𝖻𝗈𝗑 𝖺𝗇𝖽 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗌𝗁𝖺𝗋𝖺𝖻𝗅𝖾 𝗅𝗂𝗇𝗄.
 
 ✧ `/𝗍𝗀𝗍` : 𝖯𝗋𝗈𝗏𝗂𝖽𝖾 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗍𝖾𝗑𝗍 𝗆𝖾𝗌𝗌𝖺𝗀𝖾, 𝖺𝗇𝖽 𝗍𝗁𝖾 𝖻𝗈𝗍 𝗐𝗂𝗅𝗅 𝗎𝗉𝗅𝗈𝖺𝖽 𝗂𝗍 𝗍𝗈 𝖯𝖺𝗌𝗍𝖾𝖻𝗂𝗇 𝖺𝗇𝖽 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖺 𝗌𝗁𝖺𝗋𝖺𝖻𝗅𝖾 𝗅𝗂𝗇𝗄.
 
- **𝖴𝗌𝖺𝗀𝖾:**

   𝟣. **𝖬𝖾𝖽𝗂𝖺 𝖴𝗉𝗅𝗈𝖺𝖽:**
      - 𝖱𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺𝗇𝗒 𝗌𝗎𝗉𝗉𝗈𝗋𝗍𝖾𝖽 𝗆𝖾𝖽𝗂𝖺 𝗎𝗌𝗂𝗇𝗀 𝗍𝗁𝖾 `/𝗍𝗀𝗆` 𝖼𝗈𝗆𝗆𝖺𝗇𝖽.
       - 𝖲𝗎𝗉𝗉𝗈𝗋𝗍𝖾𝖽 𝗆𝖾𝖽𝗂𝖺: 𝗉𝗁𝗈𝗍𝗈𝗌, 𝗏𝗂𝖽𝖾𝗈𝗌, 𝖺𝗎𝖽𝗂𝗈, 𝖽𝗈𝖼𝗎𝗆𝖾𝗇𝗍𝗌, 𝖺𝗇𝗂𝗆𝖺𝗍𝗂𝗈𝗇𝗌, 𝖦𝖨𝖥𝗌, 𝗌𝗍𝗂𝖼𝗄𝖾𝗋𝗌, 𝗏𝗈𝗂𝖼𝖾 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌, 𝗏𝗂𝖽𝖾𝗈 𝗇𝗈𝗍𝖾𝗌
       - 𝖳𝗁𝖾 𝖻𝗈𝗍 𝖽𝗈𝗐𝗇𝗅𝗈𝖺𝖽𝗌 𝗍𝗁𝖾 𝗆𝖾𝖽𝗂𝖺 𝖺𝗇𝖽 𝗎𝗉𝗅𝗈𝖺𝖽𝗌 𝗂𝗍 𝗍𝗈 𝗍𝗁𝖾 𝖢𝖺𝗍𝖻𝗈𝗑 𝖠𝖯𝖨.
       - 𝖠 𝗅𝗂𝗇𝗄 𝗍𝗈 𝗍𝗁𝖾 𝗎𝗉𝗅𝗈𝖺𝖽𝖾𝖽 𝗆𝖾𝖽𝗂𝖺 𝗂𝗌 𝗋𝖾𝗍𝗎𝗋𝗇𝖾𝖽 𝖺𝗅𝗈𝗇𝗀 𝗐𝗂𝗍𝗁 𝖺 𝗌𝗁𝖺𝗋𝖾 𝖻𝗎𝗍𝗍𝗈𝗇.
 
   𝟤. **𝖳𝖾𝗑𝗍 𝖴𝗉𝗅𝗈𝖺𝖽:**
      - 𝖴𝗌𝖾 `/𝗍𝗀𝗍 <𝗍𝖾𝗑𝗍>` 𝗈𝗋 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗍𝖾𝗑𝗍 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗐𝗂𝗍𝗁 `/𝗍𝗀𝗍`.
       - 𝖳𝗁𝖾 𝖻𝗈𝗍 𝗎𝗉𝗅𝗈𝖺𝖽𝗌 𝗍𝗁𝖾 𝗉𝗋𝗈𝗏𝗂𝖽𝖾𝖽 𝗍𝖾𝗑𝗍 𝗍𝗈 𝖯𝖺𝗌𝗍𝖾𝖻𝗂𝗇.
       - 𝖠 𝗅𝗂𝗇𝗄 𝗍𝗈 𝗍𝗁𝖾 𝖯𝖺𝗌𝗍𝖾𝖻𝗂𝗇 𝗉𝖺𝗀𝖾 𝗂𝗌 𝗋𝖾𝗍𝗎𝗋𝗇𝖾𝖽 𝖺𝗅𝗈𝗇𝗀 𝗐𝗂𝗍𝗁 𝖺 𝗌𝗁𝖺𝗋𝖾 𝖻𝗎𝗍𝗍𝗈𝗇.
 """
