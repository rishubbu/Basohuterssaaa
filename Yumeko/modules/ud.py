import requests
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Yumeko import app
from config import config 

@app.on_message(filters.command("ud") | filters.command("ud", prefixes= config.COMMAND_PREFIXES))
async def ud_(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("𝖯𝗅𝖾𝖺𝗌𝖾 𝖾𝗇𝗍𝖾𝗋 𝗄𝖾𝗒𝗐𝗈𝗋𝖽𝗌 𝗍𝗈 𝗌𝖾𝖺𝗋𝖼𝗁 𝗈𝗇 𝗎𝖽!")

    text = message.text.split(None, 1)[1]
    url = f"https://api.urbandictionary.com/v0/define?term={text}"
    
    try:
        response = requests.get(url)
        results = response.json()
    except Exception as e:
        return await message.reply_text(f"Error: {e}")

    if results.get("list"):
        definition = results["list"][0].get("definition", "")
        example = results["list"][0].get("example", "")
        definition = definition.replace("[", "").replace("]", "")
        example = example.replace("[", "").replace("]", "")

        reply_txt = f'𝖶𝗈𝗋𝖽: {text}\n\n𝖣𝖾𝖿𝗂𝗇𝗂𝗍𝗂𝗈𝗇:\n{definition}\n\n𝖤𝗑𝖺𝗆𝗉𝗅𝖾:\n{example}'
    else:
        reply_txt = f'𝖶𝗈𝗋𝖽: {text}\n\n𝖱𝖾𝗌𝗎𝗅𝗍𝗌: 𝖲𝗈𝗋𝗋𝗒, 𝖼𝗈𝗎𝗅𝖽 𝗇𝗈𝗍 𝖿𝗂𝗇𝖽 𝖺𝗇𝗒 𝗆𝖺𝗍𝖼𝗁𝗂𝗇𝗀 𝗋𝖾𝗌𝗎𝗅𝗍𝗌!'

    google_search_url = f"https://www.google.com/search?q={text}"
    
    # Create inline keyboard with Google search button
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔎 𝖦𝗈𝗈𝗀𝗅𝖾 𝗂𝗍!", url=google_search_url)]]
    )
    
    await message.reply_text(reply_txt, reply_markup=keyboard)

__module__ = "𝖴𝗋𝖻𝖺𝗇 𝖣𝗂𝖼𝗍𝗂𝗈𝗇𝖺𝗋𝗒"


__help__ = """**𝖴𝗋𝖻𝖺𝗇 𝖣𝗂𝖼𝗍𝗂𝗈𝗇𝖺𝗋𝗒 𝖫𝗈𝗈𝗄𝗎𝗉**

- **𝖢𝗈𝗆𝗆𝖺𝗇𝖽:**
  ✧ `/𝗎𝖽 <𝗐𝗈𝗋𝖽>` **:** 𝖥𝖾𝗍𝖼𝗁 𝗍𝗁𝖾 𝖽𝖾𝖿𝗂𝗇𝗂𝗍𝗂𝗈𝗇 𝖺𝗇𝖽 𝖾��𝖺𝗆𝗉𝗅𝖾 𝗎𝗌𝖺𝗀𝖾 𝗈𝖿 𝖺 𝗐𝗈𝗋𝖽 𝖿𝗋𝗈𝗆 𝖴𝗋𝖻𝖺𝗇 𝖣𝗂𝖼𝗍𝗂𝗈𝗇𝖺𝗋𝗒.
 
- **𝖣𝖾𝗍𝖺𝗂𝗅𝗌:**
  ✧ 𝖲𝖾𝖺𝗋𝖼𝗁𝖾𝗌 𝖿𝗈𝗋 𝗍𝗁𝖾 𝗀𝗂𝗏𝖾𝗇 𝗄𝖾𝗒𝗐𝗈𝗋𝖽 𝗈𝗇 𝖴𝗋𝖻𝖺𝗇 𝖣𝗂𝖼𝗍𝗂𝗈𝗇𝖺𝗋𝗒.
   ✧ 𝖨𝖿 𝗇𝗈 𝗋𝖾𝗌𝗎𝗅𝗍𝗌 𝖺𝗋𝖾 𝖿𝗈𝗎𝗇𝖽, 𝗂𝗍 𝗐𝗂𝗅𝗅 𝗇𝗈𝗍𝗂𝖿𝗒 𝗒𝗈𝗎.
   ✧ 𝖯𝗋𝗈𝗏𝗂𝖽𝖾𝗌 𝖺𝗇 𝗈𝗉𝗍𝗂𝗈𝗇 𝗍𝗈 𝖦𝗈𝗈𝗀𝗅𝖾 𝗍𝗁𝖾 𝗐𝗈𝗋𝖽 𝖿𝗈𝗋 𝗆𝗈𝗋𝖾 ��𝗈𝗇𝗍𝖾𝗑𝗍.
 """