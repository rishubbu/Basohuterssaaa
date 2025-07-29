import random
from pyrogram import filters
from pyrogram.types import Message
from Yumeko import app
from Yumeko.vars import GIF

@app.on_message(filters.command("wish"))
async def wish(client, message: Message):
    if message.reply_to_message:
        mm = random.randint(1, 100)
        reply_message = message.reply_to_message
        fire = "https://telegra.ph/file/d6c2cd346255a33b3a023.mp4"
        await client.send_video(
            message.chat.id,
            fire,
            caption=f"**𝖧𝖾𝗅𝗅𝗈, {message.from_user.first_name}! 𝖳𝗈 𝗆𝖺𝗄𝖾 𝖺 𝗐𝗂𝗌𝗁, 𝗉𝗅𝖾𝖺𝗌𝖾 𝗎𝗌𝖾 𝗍𝗁𝖾 𝖿𝗈𝗋𝗆𝖺𝗍 /𝗐𝗂𝗌𝗁 (𝖸𝗈𝗎𝗋 𝖶𝗂𝗌𝗁) 🙃**",
            reply_to_message_id=reply_message.id,
        )
    elif len(message.command) > 1:
        mm = random.randint(1, 100)
        wish_text = message.text.split(None, 1)[1]
        fire = random.choice(GIF)
        await client.send_video(
            message.chat.id,
            fire,
            caption=f"**❄️ 𝖧ᴇʏ! {message.from_user.first_name}, ʏᴏᴜʀ ᴡɪsʜ ʜᴀs ʙᴇᴇɴ ᴄᴀsᴛᴇᴅ\n✨ ʏᴏᴜʀ ᴡɪꜱʜ : {wish_text}\n🫧 ᴘᴏssɪʙɪʟɪᴛɪᴇs : {mm}%**",
            reply_to_message_id=message.id,
        )
    else:
        await client.send_message(
            message.chat.id,
            "𝖯𝗅𝖾𝖺𝗌𝖾 𝗍𝖾𝗅𝗅 𝗆𝖾 𝗒𝗈𝗎𝗋 𝗐𝗂𝗌𝗁 𝖻𝗒 𝗎𝗌𝗂𝗇𝗀 𝗍𝗁𝖾 𝖿𝗈𝗋𝗆𝖺𝗍 /𝗐𝗂𝗌𝗁 (𝖸𝗈𝗎𝗋 𝖶𝗂𝗌𝗁)",
            reply_to_message_id=message.id,
        )
        
        
__module__ = "𝖶𝗂𝗌𝗁"


__help__ = """**𝖬𝖺𝗄𝖾 𝖺 𝖶𝗂𝗌𝗁 𝖺𝗇𝖽 𝖢𝗁𝖾𝖼𝗄 𝖨𝗍𝗌 𝖯𝗈𝗌𝗌𝗂𝖻𝗂𝗅𝗂𝗍𝗒!**

- **𝖢𝗈𝗆𝗆𝖺𝗇𝖽:**
  ✧ `/𝗐𝗂𝗌𝗁 <𝗒𝗈𝗎𝗋 𝗐𝗂𝗌𝗁>` **:** ��𝖺𝗌𝗍 𝖺 𝗐𝗂𝗌𝗁 𝖺𝗇𝖽 𝗀𝖾𝗍 𝖺 𝗋𝖺𝗇𝖽𝗈𝗆𝗂𝗓𝖾𝖽 𝗉𝗈𝗌𝗌𝗂𝖻𝗂𝗅𝗂𝗍𝗒 𝗉𝖾𝗋𝖼𝖾𝗇𝗍𝖺𝗀𝖾.
   ✧ 𝖱𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗐𝗂𝗍𝗁 `/𝗐𝗂𝗌𝗁` 𝗍𝗈 𝗌𝖾𝗇𝖽 𝖺 𝗐𝗂𝗌𝗁-𝗋𝖾𝗅𝖺𝗍𝖾𝖽 𝖺𝗇𝗂𝗆𝖺𝗍𝗂𝗈𝗇.
 
- **𝖣𝖾𝗍𝖺𝗂𝗅𝗌:**
  ✧ 𝖨𝖿 𝗇𝗈 𝗐𝗂𝗌𝗁 𝗂𝗌 𝗉𝗋𝗈𝗏𝗂𝖽𝖾𝖽, 𝗍𝗁𝖾 𝖻𝗈𝗍 𝗐𝗂𝗅𝗅 𝗉𝗋𝗈𝗆𝗉𝗍 𝗒𝗈𝗎 𝗍𝗈 𝗂𝗇𝖼𝗅𝗎𝖽𝖾 𝗈𝗇𝖾.
   ✧ 𝖶𝗁𝖾𝗇 𝗎𝗌𝖾𝖽 𝗐𝗂𝗍𝗁 𝖺 𝗐𝗂𝗌𝗁, 𝗍𝗁𝖾 𝖻𝗈𝗍 𝗐𝗂𝗅𝗅 𝗋𝖾𝗌𝗉𝗈𝗇𝖽 𝗐𝗂𝗍𝗁 𝖺 𝗋𝖺𝗇𝖽𝗈𝗆 𝖦𝖨𝖥 𝖺𝗇𝖽 𝗍𝗁𝖾 𝖼𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝖾𝖽 𝗉𝗈𝗌𝗌𝗂𝖻𝗂𝗅𝗂𝗍𝗒 𝗈𝖿 𝗒𝗈𝗎𝗋 𝗐𝗂𝗌𝗁 𝖼𝗈𝗆𝗂𝗇�� 𝗍𝗋𝗎𝖾.
 
"""

