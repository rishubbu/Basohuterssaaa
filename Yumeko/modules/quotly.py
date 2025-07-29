import os
import base64
import json
from PIL import Image
from json.decoder import JSONDecodeError
from random import choice
import asyncio
from pyrogram import filters
from Yumeko import app
import aiohttp
from pyrogram.types import Message

try:
    from PIL import Image
except ImportError:
    Image = None

# Example color palette for backgrounds
all_col = ["#FFFFFF", "#FF5733", "#33FF57", "#3357FF", "#9C27B0", "#2196F3", "#FF9800", "#607D8B", "#E91E63", "#4CAF50"]

# Animation styles
animation_styles = ["slide", "fade", "pop", "bounce"]

class Quotly:
    _API = "https://bot.lyo.su/quote/generate"
    _entities = {
        "mention": "mention",
        "bold": "bold",
        "italic": "italic",
        "underline": "underline",
        "strikethrough": "strikethrough",
        "code": "code",
        "pre": "pre",
        "text_link": "text_link",
        "text_mention": "text_mention",
    }

    async def _format_quote(self, message, reply=None, sender=None, type_="private", custom_text=None, style_options=None):
        async def telegraph(file_):
            file = file_ + ".png"
            Image.open(file_).save(file, "PNG")
            files = {"file": open(file, "rb").read()}
            uri = (
                "https://telegra.ph"
                + (
                    await async_searcher(
                        "https://telegra.ph/upload", post=True, data=files, re_json=True
                    )
                )[0]["src"]
            )
            os.remove(file)
            os.remove(file_)
            return uri

        if reply:
            reply = {
                "name": reply.from_user.first_name if reply.from_user else "Deleted Account",
                "text": reply.text or reply.caption or "",
                "chatId": reply.chat.id,
            }
        else:
            reply = {}
            
        is_forward = message.forward_from or message.forward_from_chat
        name = None
        last_name = None
        
        if sender:
            id_ = sender.id
            name = sender.first_name
            last_name = sender.last_name
        elif not is_forward:
            id_ = message.from_user.id if message.from_user else None
            sender = message.from_user
            name = sender.first_name if sender else None
        else:
            id_ = None
            sender = None
            if message.forward_from:
                id_ = message.forward_from.id
                name = message.forward_from.first_name
                sender = message.forward_from
            elif message.forward_sender_name:
                name = message.forward_sender_name
            
        if sender and hasattr(sender, "last_name"):
            last_name = sender.last_name
            
        # Process entities
        entities = []
        if message.entities:
            for entity in message.entities:
                entity_type = entity.type.name.lower()
                if entity_type in self._entities:
                    enti_ = {
                        "offset": entity.offset,
                        "length": entity.length,
                        "type": self._entities[entity_type]
                    }
                    if entity_type == "text_link":
                        enti_["url"] = entity.url
                    elif entity_type == "text_mention" and entity.user:
                        enti_["user"] = {
                            "id": entity.user.id,
                            "first_name": entity.user.first_name,
                            "last_name": entity.user.last_name,
                            "username": entity.user.username
                        }
                    entities.append(enti_)
                    
        message_dict = {
            "entities": entities,
            "chatId": id_,
            "avatar": True,
            "from": {
                "id": id_,
                "first_name": (name or (sender.first_name if sender else None))
                or "Deleted Account",
                "last_name": last_name,
                "username": sender.username if sender else None,
                "language_code": "en",
                "title": name,
                "name": name or "Unknown",
                "type": type_,
            },
            "text": custom_text if custom_text is not None else (message.text or message.caption or ""),
            "replyMessage": reply,
        }
        
        # Apply style options if provided
        if style_options:
            for key, value in style_options.items():
                message_dict[key] = value
        
        # Handle media thumbnails
        if message.document and message.document.thumbs:
            file_ = await message.download(file_name="thumb.jpg")
            uri = await telegraph(file_)
            message_dict["media"] = {"url": uri}

        return message_dict

    async def create_quotly(
        self,
        message,
        url="https://qoute-api-akashpattnaik.koyeb.app/generate",
        reply={},
        bg=None,
        sender=None,
        OQAPI=True,
        file_name="quote.webp",
        custom_text=None,
        style_options=None,
        animated=False,
        animation_style=None,
        bg_image=None,
    ):
        """Create quotely's quote."""
        if not isinstance(message, list):
            message = [message]
        if OQAPI:
            url = Quotly._API
        if not bg and not bg_image:
            bg = "#1b1429"
            
        # Set output format based on animation
        output_format = "gif" if animated else "webp"
        file_name = "quote.gif" if animated else file_name
            
        content = {
            "type": "quote",
            "format": output_format,
            "width": 512,
            "height": 768,
            "scale": 2,
            "messages": [
                await self._format_quote(
                    msg, 
                    reply=reply, 
                    sender=sender, 
                    custom_text=custom_text if i == 0 else None,
                    style_options=style_options if i == 0 else None
                )
                for i, msg in enumerate(message)
            ],
        }
        
        # Add background color or image
        if bg_image:
            content["backgroundImage"] = bg_image
        else:
            content["backgroundColor"] = bg
        
        # Add animation parameters if needed
        if animated:
            content["animated"] = True
            if animation_style and animation_style in animation_styles:
                content["animationStyle"] = animation_style
        
        try:
            request = await async_searcher(url, post=True, json=content, re_json=True)
        except Exception as er:
            if url != self._API:
                return await self.create_quotly(
                    self._API, post=True, json=content, re_json=True
                )
            raise er
        if request.get("ok"):
            with open(file_name, "wb") as file:
                image = base64.decodebytes(request["result"]["image"].encode("utf-8"))
                file.write(image)
            return file_name
        raise Exception(str(request))

    async def create_custom_quote(
        self,
        message,
        custom_text,
        bg=None,
        reply=None,
        sender=None,
        file_name="quote.webp",
        style_options=None,
        animated=False,
        animation_style=None,
        bg_image=None,
    ):
        """Create a quote with custom text."""
        return await self.create_quotly(
            message,
            reply=reply,
            bg=bg,
            sender=sender,
            file_name=file_name,
            custom_text=custom_text,
            style_options=style_options,
            animated=animated,
            animation_style=animation_style,
            bg_image=bg_image,
        )

quotly = Quotly()

async def async_searcher(
    url: str,
    post: bool = None,
    headers: dict = None,
    params: dict = None,
    json: dict = None,
    data: dict = None,
    ssl=None,
    re_json: bool = False,
    re_content: bool = False,
    real: bool = False,
    *args,
    **kwargs,
):
    async with aiohttp.ClientSession(headers=headers) as client:
        if post:
            data = await client.post(
                url, json=json, data=data, ssl=ssl, *args, **kwargs
            )
        else:
            data = await client.get(url, params=params, ssl=ssl, *args, **kwargs)
        if re_json:
            return await data.json()
        if re_content:
            return await data.read()
        if real:
            return data
        return await data.text()

def json_parser(data, indent=None, ascii=False):
    parsed = {}
    try:
        if isinstance(data, str):
            parsed = json.loads(str(data))
            if indent:
                parsed = json.dumps(
                    json.loads(str(data)), indent=indent, ensure_ascii=ascii
                )
        elif isinstance(data, dict):
            parsed = data
            if indent:
                parsed = json.dumps(data, indent=indent, ensure_ascii=ascii)
    except JSONDecodeError:
        parsed = eval(data)
    return parsed

def check_filename(filroid):
    if os.path.exists(filroid):
        no = 1
        while True:
            ult = "{0}_{2}{1}".format(*os.path.splitext(filroid) + (no,))
            if os.path.exists(ult):
                no += 1
            else:
                return ult
    return filroid

# Helper function to edit or reply to messages
async def eor(message, text=None, **args):
    time = args.pop("time", None)
    edit_time = args.pop("edit_time", None)
    
    if "link_preview" not in args:
        args["disable_web_page_preview"] = True
    
    reply_to = message.reply_to_message_id or message.id
    
    if message.from_user and message.from_user.is_self:
        if edit_time:
            await asyncio.sleep(edit_time)
        
        if "file" in args and args["file"] and not message.media:
            await message.delete()
            try:
                ok = await app.send_message(message.chat.id, text, reply_to_message_id=reply_to, **args)
            except Exception:
                pass
        else:
            try:
                ok = await message.edit(text, **args)
            except Exception:
                pass
    else:
        ok = await app.send_message(message.chat.id, text, reply_to_message_id=reply_to, **args)

    if time:
        await asyncio.sleep(time)
        return await ok.delete()
    return ok

async def eod(message, text=None, **kwargs):
    kwargs["time"] = kwargs.get("time", 8)
    return await eor(message, text, **kwargs)

async def _try_delete(message):
    try:
        return await message.delete()
    except Exception as er:
        print(er)

# Register the command handler
@app.on_message(filters.command("q"))
async def quott_(client, message):
    match = message.text.split(None, 1)[1].strip() if len(message.text.split()) > 1 else ""
    
    if not message.reply_to_message:
        return await message.reply("Please reply to a message to generate a quote")
    
    # Check if animated quote is requested
    animated = False
    animation_style = None
    bg_image = None
    
    if "-anim" in match:
        animated = True
        match = match.replace("-anim", "").strip()
        
        # Check for animation style
        for style in animation_styles:
            if f"-{style}" in match:
                animation_style = style
                match = match.replace(f"-{style}", "").strip()
    
    # Check for image background
    if "-img" in match:
        parts = match.split("-img", 1)
        match = parts[0].strip()
        
        # If there's a URL after -img
        if len(parts) > 1 and parts[1].strip():
            bg_image = parts[1].strip()
            # If URL is not properly formatted, add https://
            if not bg_image.startswith(("http://", "https://")):
                bg_image = "https://" + bg_image
    
    msg = await message.reply("Creating quote please wait...")
    reply = message.reply_to_message
    replied_to, reply_ = None, None
    
    if match:
        spli_ = match.split(maxsplit=1)
        if (spli_[0] in ["r", "reply"]) or (
            spli_[0].isdigit() and int(spli_[0]) in range(1, 21)
        ):
            if spli_[0].isdigit():
                # Get multiple messages
                if not client.me.is_bot:
                    # For user accounts
                    reply_ = []
                    async for msg in client.get_chat_history(
                        message.chat.id, 
                        limit=int(spli_[0]),
                        offset_id=message.reply_to_message_id
                    ):
                        if msg.id < message.reply_to_message_id:
                            reply_.append(msg)
                else:
                    # For bot accounts - more limited
                    id_ = reply.id
                    reply_ = []
                    # This is a simplified approach - bots can't easily get message history
                    # You may need to implement a custom solution based on your needs
                    for i in range(int(spli_[0])):
                        try:
                            msg_id = id_ - i - 1
                            if msg_id > 0:
                                msh = await client.get_messages(message.chat.id, msg_id)
                                if msh:
                                    reply_.append(msh)
                        except Exception:
                            pass
            else:
                # Get the replied-to message
                if reply.reply_to_message_id:
                    replied_to = await client.get_messages(
                        message.chat.id, 
                        reply.reply_to_message_id
                    )
            
            try:
                match = spli_[1]
            except IndexError:
                match = None
    
    user = None
    if not reply_:
        reply_ = reply
    
    if match:
        match = match.split(maxsplit=1)
    
    if match:
        if match[0].startswith("@") or match[0].isdigit():
            try:
                user = await client.get_users(match[0])
            except Exception:
                pass
            match = match[1] if len(match) == 2 else None
        else:
            match = match[0]
    
    if match == "random":
        match = choice(all_col)
    
    try:
        file = await quotly.create_quotly(
            reply_, 
            bg=match, 
            reply=replied_to, 
            sender=user,
            animated=animated,
            animation_style=animation_style,
            bg_image=bg_image
        )
    except Exception as er:
        return await msg.edit(str(er))
    
    await reply.reply_document(file)
    os.remove(file)
    await msg.delete()

# New command for custom quotes
@app.on_message(filters.command("qt"))
async def custom_quote(client, message: Message):
    if not message.reply_to_message:
        return await message.reply("Please reply to a message to create a custom quote")
    
    # Parse command arguments
    args = message.text.split(None, 1)
    if len(args) < 2:
        return await message.reply("Please provide the custom text for the quote")
    
    custom_text = args[1]
    
    # Check for background color
    bg_color = None
    bg_image = None
    
    if " -bg " in custom_text:
        parts = custom_text.split(" -bg ", 1)
        custom_text = parts[0].strip()
        bg_color = parts[1].strip().split()[0] if " " in parts[1] else parts[1].strip()
        
        if bg_color == "random":
            bg_color = choice(all_col)
    
    # Check for image background
    if " -img " in custom_text:
        parts = custom_text.split(" -img ", 1)
        custom_text = parts[0].strip()
        
        if len(parts) > 1:
            bg_image = parts[1].strip().split()[0] if " " in parts[1] else parts[1].strip()
            # If URL is not properly formatted, add https://
            if not bg_image.startswith(("http://", "https://")):
                bg_image = "https://" + bg_image
            # If image URL is provided, ignore background color
            bg_color = None
    
    # Check for style options
    style_options = {}
    
    # Check for font size option
    if " -size " in custom_text:
        parts = custom_text.split(" -size ", 1)
        custom_text = parts[0].strip()
        try:
            size = int(parts[1].strip().split()[0])
            style_options["fontSize"] = size
        except (ValueError, IndexError):
            pass
    
    # Check for text color option
    if " -color " in custom_text:
        parts = custom_text.split(" -color ", 1)
        custom_text = parts[0].strip()
        try:
            color = parts[1].strip().split()[0]
            style_options["textColor"] = color
        except IndexError:
            pass
    
    # Check for bold text option
    if " -bold" in custom_text:
        custom_text = custom_text.replace(" -bold", "")
        style_options["bold"] = True
    
    # Check for animation
    animated = False
    animation_style = None
    
    if " -anim" in custom_text:
        animated = True
        custom_text = custom_text.replace(" -anim", "")
        
        # Check for animation style
        for style in animation_styles:
            if f" -{style}" in custom_text:
                animation_style = style
                custom_text = custom_text.replace(f" -{style}", "")
    
    msg = await message.reply("Creating custom quote please wait...")
    reply = message.reply_to_message
    
    # Check for user attribution
    user = None
    if " -u " in custom_text:
        parts = custom_text.split(" -u ", 1)
        custom_text = parts[0].strip()
        user_id = parts[1].strip().split()[0]
        
        try:
            if user_id.startswith("@") or user_id.isdigit():
                user = await client.get_users(user_id)
        except Exception:
            pass
    
    try:
        file = await quotly.create_custom_quote(
            reply, 
            custom_text=custom_text,
            bg=bg_color,
            sender=user,
            style_options=style_options,
            animated=animated,
            animation_style=animation_style,
            bg_image=bg_image
        )
    except Exception as er:
        return await msg.edit(str(er))
    
    await reply.reply_document(file)
    os.remove(file)
    await msg.delete()


__module__ = "𝖰𝗎𝗈𝗍𝗅𝗒"

__help__ = """**𝖢𝗋𝖾𝖺𝗍𝖾 𝖻𝖾𝖺𝗎𝗍𝗂𝖿𝗎𝗅 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗊𝗎𝗈𝗍𝖾𝗌:**

    ✧ `/𝗊` : 𝖱𝖾𝗉𝗅𝗒 𝗍𝗈 𝖺 𝗆𝖾𝗌𝗌𝖺𝗀𝖾 𝗐𝗂𝗍𝗁 𝗍𝗁𝗂𝗌 𝖼𝗈𝗆𝗆𝖺𝗇𝖽 𝗍𝗈 𝗀𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾.
    ✧ `/𝗊 <𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽 𝖼𝗈𝗅𝗈𝗋>` : 𝖢𝗎𝗌𝗍𝗈𝗆𝗂𝗓𝖾 𝗍𝗁𝖾 𝗊𝗎𝗈𝗍𝖾'𝗌 𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽 𝖼𝗈𝗅𝗈𝗋 𝗎𝗌𝗂𝗇𝗀 𝖺 𝗁𝖾𝗑 𝖼𝗈𝖽𝖾 𝗈𝗋 𝖺 𝖼𝗈𝗅𝗈𝗋 𝗇𝖺𝗆𝖾 (𝖾.𝗀., `/𝗊 #𝖥𝖥𝟧𝟩𝟥𝟥`).
    ✧ `/𝗊 𝗋𝖺𝗇𝖽𝗈𝗆` : 𝖦𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗐𝗂𝗍𝗁 𝖺 𝗋𝖺𝗇𝖽𝗈𝗆 𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽 𝖼𝗈𝗅𝗈𝗋.
    ✧ `/𝗊 <𝗇𝗎𝗆𝖻𝖾𝗋>` : 𝖦𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗂𝗇𝖼𝗅𝗎𝖽𝗂𝗇𝗀 𝗍𝗁𝖾 𝗌𝗉𝖾𝖼𝗂𝖿𝗂𝖾𝖽 𝗇𝗎𝗆𝖻𝖾𝗋 𝗈𝖿 𝗉𝗋𝖾𝗏𝗂𝗈𝗎𝗌 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌 (𝖾.𝗀., `/𝗊 𝟧` 𝗍𝗈 𝗂𝗇𝖼𝗅𝗎𝖽𝖾 𝟧 𝗆𝖾𝗌𝗌𝖺𝗀𝖾𝗌).
    ✧ `/𝗊 𝗋` : 𝖦𝖾𝗇𝖾𝗋𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗍𝗁𝖺𝗍 𝗂𝗇𝖼𝗅𝗎𝖽𝖾𝗌 𝗍𝗁𝖾 𝗋𝖾𝗉𝗅𝗂𝖾𝖽-𝗍𝗈 𝗆𝖾𝗌𝗌𝖺𝗀𝖾.
    ✧ `/𝗊 -𝖺𝗇𝗂𝗆` : 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺𝗇 𝖺𝗇𝗂𝗆𝖺𝗍𝖾𝖽 𝗊𝗎𝗈𝗍𝖾.
    ✧ `/𝗊 -𝖺𝗇𝗂𝗆 -𝗌𝗅𝗂𝖽𝖾` : 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺𝗇 𝖺𝗇𝗂𝗆𝖺𝗍𝖾𝖽 𝗊𝗎𝗈𝗍𝖾 𝗐𝗂𝗍𝗁 𝗌𝗅𝗂𝖽𝖾 𝖺𝗇𝗂𝗆𝖺𝗍𝗂𝗈𝗇 (𝗈𝗉𝗍𝗂𝗈𝗇𝗌: 𝗌𝗅𝗂𝖽𝖾, 𝖿𝖺𝖽𝖾, 𝗉𝗈𝗉, 𝖻𝗈𝗎𝗇𝖼𝖾).
 
   
**𝖢𝗎𝗌𝗍𝗈𝗆 𝖰𝗎𝗈𝗍𝖾𝗌:**
   ✧ `/𝗊𝗍 <𝗍𝖾𝗑𝗍>` : 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗐𝗂𝗍𝗁 𝖼𝗎𝗌𝗍𝗈𝗆 𝗍𝖾𝗑𝗍 𝗐𝗁𝗂𝗅𝖾 𝗄𝖾𝖾𝗉𝗂𝗇𝗀 𝗍𝗁𝖾 𝗈𝗋𝗂𝗀𝗂𝗇𝖺𝗅 𝗌𝖾𝗇𝖽𝖾𝗋.
    
 
**𝖤𝗑𝖺𝗆𝗉𝗅𝖾𝗌:**
   ✧ `/𝗊` : 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝖿𝗋𝗈𝗆 𝗍𝗁𝖾 𝗋𝖾𝗉𝗅𝗂𝖾𝖽 𝗆𝖾𝗌𝗌𝖺𝗀𝖾.
   ✧ `/𝗊 #𝟣𝖻𝟣𝟦𝟤𝟫` : 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺 𝗊𝗎𝗈𝗍𝖾 𝗐𝗂𝗍𝗁 𝖺 𝖽𝖺𝗋𝗄 𝗉𝗎𝗋𝗉𝗅𝖾 𝖻𝖺𝖼𝗄𝗀𝗋𝗈𝗎𝗇𝖽.
   ✧ `/𝗊𝗍 𝖨 𝗇𝖾𝗏𝖾𝗋 𝗌𝖺𝗂𝖽 𝗍𝗁𝖺𝗍!` : 𝖢𝗋𝖾𝖺𝗍𝖾 𝖺 𝖿𝖺𝗄𝖾 𝗊𝗎𝗈𝗍𝖾 𝗐𝗂𝗍𝗁 𝖼𝗎𝗌𝗍𝗈𝗆 𝗍𝖾𝗑𝗍.
"""