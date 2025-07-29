import asyncio
import random
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ChatType
from Yumeko import app

# Define emojis list since we couldn't find the original one
emojis = [
    "👍", "👋", "🙏", "🤝", "💪", "❤️", "🔥", "⚡️", "🌟", "🎉", "✨", "🎊", "🎁", "🎈", "🎯", "🏆", "🥇", "🏅", "🔔", "📢",
    "💖", "💎", "🚀", "🎶", "🎵", "🎤", "🎧", "🥳", "😎", "😁", "🙌", "👏", "🤩", "🎮", "📌", "📝", "📊", "💡", "🔑", "🔗",
    "🕹️", "💰", "🎀", "🏅", "🥈", "🥉", "📈", "📉", "⏳", "⏰", "🕛", "🕺", "💃", "🎯", "🛡️", "🎗️", "🖥️", "🛠️", "🔧", "💼"
]


spam_chats = []

@app.on_message(filters.command(["tagall", "etagall"]) | filters.command(["all", "eall"], prefixes="@"))
async def mentionall(client, message: Message):
    chat_id = message.chat.id
    
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("𝖳𝗁𝗂𝗌 𝖼𝗈𝗆𝗆𝖺𝗇𝖽 𝖼𝖺𝗇 𝖻𝖾 𝗎𝗌𝖾𝖽 𝗂𝗇 𝗀𝗋𝗈𝗎𝗉𝗌 𝖺𝗇𝖽 𝖼𝗁𝖺𝗇𝗇𝖾𝗅𝗌!")

    # Check if user is admin
    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    if user_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await message.reply_text("𝖮𝗇𝗅𝗒 𝖺𝖽𝗆𝗂𝗇𝗌 𝖼𝖺𝗇 𝗆𝖾𝗇𝗍𝗂𝗈𝗇 𝖺𝗅𝗅!")

    # Determine the command type
    command = message.command[0] if message.command else ""
    command_type = command.lower()
    
    # Get the message text
    if len(message.command) > 1:
        msg_text = message.text.split(None, 1)[1]
    else:
        msg_text = ""
    
    if msg_text and message.reply_to_message:
        return await message.reply_text("𝖯𝗋𝗈𝗏𝗂𝖽𝖾 𝗈𝗇𝗅𝗒 𝗈𝗇𝖾 𝖺𝗋𝗀𝗎𝗆𝖾𝗇𝗍!")
    elif message.reply_to_message:
        msg = message.reply_to_message
        mode = "text_on_reply"
    elif msg_text:
        msg = msg_text
        mode = "text_on_cmd"
    else:
        return await message.reply_text("𝖱𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗈𝗋 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝗍𝖾𝗑𝗍 𝗍𝗈 𝗆𝖾𝗇𝗍𝗂𝗈𝗇 𝗈𝗍𝗁𝖾𝗋𝗌!")

    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""
    
    async for usr in client.get_chat_members(chat_id):
        if chat_id not in spam_chats:
            break
            
        if usr.user.is_bot or usr.user.is_deleted:
            continue
            
        usrnum += 1

        if command_type in ["all", "tagall"]:
            usrtxt += f"[{usr.user.first_name}](tg://user?id={usr.user.id}), "
        elif command_type in ["eall", "etagall"]:
            random_emoji = random.choice(emojis)
            usrtxt += f"[{random_emoji}](tg://user?id={usr.user.id}), "
        
        if usrnum == 5:
            if mode == "text_on_cmd":
                txt = f"{msg}\n{usrtxt}"
                await client.send_message(chat_id, txt)
            elif mode == "text_on_reply":
                await msg.reply(usrtxt)
            await asyncio.sleep(3)
            usrnum = 0
            usrtxt = ""
    
    # Send any remaining mentions
    if usrnum > 0:
        if mode == "text_on_cmd":
            txt = f"{msg}\n{usrtxt}"
            await client.send_message(chat_id, txt)
        elif mode == "text_on_reply":
            await msg.reply(usrtxt)

    try:
        spam_chats.remove(chat_id)
    except:
        pass

@app.on_message(filters.command("cancel"))
async def cancel_spam(client, message: Message):
    chat_id = message.chat.id
    
    if chat_id not in spam_chats:
        return await message.reply_text("𝖭𝗈 𝗈𝗇𝗀𝗈𝗂𝗇𝗀 𝗆𝖾𝗇𝗍𝗂𝗈𝗇 𝗉𝗋𝗈𝖼𝖾𝗌𝗌 𝗍𝗈 𝖼𝖺𝗇𝖼𝖾𝗅.")
    
    # Check if user is admin
    user_member = await client.get_chat_member(chat_id, message.from_user.id)
    if user_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await message.reply_text("𝖮𝗇𝗅𝗒 𝖺𝖽𝗆𝗂𝗇𝗌 𝖼𝖺𝗇 𝖾𝗑𝖾𝖼𝗎𝗍𝖾 𝗍𝗁𝗂𝗌 𝖼𝗈𝗆𝗆𝖺𝗇𝖽!")
    
    try:
        spam_chats.remove(chat_id)
    except:
        pass
    
    return await message.reply_text("𝖬𝖾𝗇𝗍𝗂𝗈𝗇𝗂𝗇𝗀 𝗉𝗋𝗈𝖼𝖾𝗌𝗌 𝗌𝗍𝗈𝗉𝗉𝖾𝖽.")


__module__ = "𝖳𝖺𝗀 𝖠𝗅𝗅"


__help__ = """**𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌 𝖿𝗈𝗋 𝖬𝖾𝗇𝗍𝗂𝗈𝗇𝗂𝗇𝗀 𝖠𝗅𝗅 𝖬𝖾𝗆𝖻𝖾𝗋𝗌:**

  ✧ `/𝗍𝖺𝗀𝖺𝗅𝗅 <𝗍𝖾𝗑𝗍>` 𝗈𝗋 `@𝖺𝗅𝗅 <𝗍𝖾𝗑𝗍>` **:** 𝖬𝖾𝗇𝗍𝗂𝗈𝗇 𝖺𝗅𝗅 𝗎𝗌𝖾𝗋𝗌 𝗂𝗇 𝗍𝗁𝖾 𝗀𝗋𝗈𝗎𝗉 𝗎𝗌𝗂𝗇𝗀 𝗍𝗁𝖾𝗂𝗋 𝗇𝖺𝗆𝖾𝗌.
   ✧ `/𝖾𝗍𝖺𝗀𝖺𝗅𝗅 <𝗍𝖾𝗑𝗍>` 𝗈𝗋 `@𝖾𝖺𝗅𝗅 <𝗍𝖾𝗑𝗍>` **:** 𝖬𝖾𝗇𝗍𝗂𝗈𝗇 𝖺𝗅𝗅 𝗎𝗌𝖾𝗋𝗌 𝗎𝗌𝗂𝗇𝗀 𝗋𝖺𝗇𝖽𝗈𝗆 𝖾𝗆𝗈𝗃𝗂𝗌 𝗂𝗇𝗌𝗍𝖾𝖺𝖽 𝗈𝖿 𝗇𝖺𝗆𝖾𝗌.
   ✧ `/𝗍𝖺𝗀𝖺𝗅𝗅` 𝗈𝗋 `/𝖾𝗍𝖺𝗀𝖺𝗅𝗅` 𝗐𝗂𝗍𝗁𝗈𝗎𝗍 𝗍𝖾𝗑𝗍 𝗐𝗈𝗋𝗄𝗌 𝖺𝗌 𝖺 𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝗆𝖾𝗇𝗍𝗂𝗈𝗇 𝗎𝗌𝖾𝗋𝗌 𝖿𝗈𝗋 𝗍𝗁𝖺𝗍 𝗆𝖾𝗌𝗌𝖺𝗀𝖾.
 
**𝖢𝖺𝗇𝖼𝖾𝗅 𝖬𝖾𝗇𝗍𝗂𝗈𝗇𝗂𝗇𝗀:**
  ✧ `/𝖼𝖺𝗇𝖼𝖾𝗅` **:** 𝖲𝗍𝗈𝗉 𝗍𝗁𝖾 𝗈𝗇𝗀𝗈𝗂𝗇𝗀 𝗆𝖾𝗇𝗍𝗂𝗈𝗇 𝗉𝗋𝗈𝖼𝖾𝗌𝗌.
 
**𝖤𝗑𝖺𝗆𝗉𝗅𝖾𝗌:**
  ✧ `/𝗍𝖺𝗀𝖺𝗅𝗅 𝖧𝖾𝗅𝗅𝗈 𝖾𝗏𝖾𝗋𝗒𝗈𝗇𝖾!` **:** 𝖬𝖾𝗇𝗍𝗂𝗈𝗇 𝖺𝗅𝗅 𝗎𝗌𝖾𝗋𝗌 𝗐𝗂𝗍𝗁 "𝖧𝖾𝗅𝗅𝗈 𝖾𝗏𝖾𝗋𝗒𝗈𝗇𝖾!" 𝗎𝗌𝗂𝗇𝗀 𝗍𝗁𝖾𝗂𝗋 𝗇𝖺𝗆𝖾𝗌.
   ✧ `/𝖾𝗍𝖺𝗀𝖺𝗅𝗅 𝖫𝖾𝗍'𝗌 𝗉𝖺𝗋𝗍𝗒!` **:** 𝖬𝖾𝗇𝗍𝗂𝗈𝗇 𝖺𝗅𝗅 𝗎𝗌𝖾𝗋𝗌 𝗐𝗂𝗍𝗁 𝗋𝖺𝗇𝖽𝗈𝗆 𝖾𝗆𝗈𝗃𝗂𝗌 𝗂𝗇𝗌𝗍𝖾𝖺𝖽 𝗈𝖿 𝗇𝖺𝗆𝖾𝗌.
   ✧ 𝖱𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗐𝗂𝗍𝗁 `/𝗍𝖺𝗀𝖺𝗅𝗅` 𝗈𝗋 `/𝖾𝗍𝖺𝗀𝖺𝗅𝗅` 𝗍𝗈 𝗆𝖾𝗇𝗍𝗂𝗈𝗇 𝖺𝗅𝗅 𝗎𝗌𝖾𝗋𝗌 𝖿𝗈𝗋 𝗍𝗁𝖺𝗍 𝗆𝖾𝗌𝗌𝖺𝗀𝖾.
 """ 