from Yumeko.database.common_chat_db import save_user_chat
from Yumeko import app, COMMON_CHAT_WATCHER_GROUP
from pyrogram.types import Message
from pyrogram import filters

@app.on_message(filters.all, group=COMMON_CHAT_WATCHER_GROUP)
async def user_chat_tracker(client, message: Message):
    user = None
    chat = None
    
    if message.from_user:
        user = message.from_user
        chat = message.chat
    elif message.sender_chat:
        user = message.sender_chat
        chat = message.chat
    

    if not user or not chat:
        return

    if user and chat:
        # Save the user-chat mapping
        await save_user_chat(user_id=user.id, chat_id=chat.id)
    else :
        return