import aiohttp
from bs4 import BeautifulSoup
from pyrogram import filters, Client
from pyrogram.types import Message
from Yumeko import app
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save
from config import config


ANIME_NEWS_NETWORK = "https://www.animenewsnetwork.com/news/"

@app.on_message(filters.command("animenews" , prefixes=config.COMMAND_PREFIXES))
@error
@save
async def anime_news(client: Client, message: Message):
    
    x = await message.reply_text("𝖥𝖾𝗍𝖼𝗁𝗂𝗇𝗀 𝗍𝗁𝖾 𝗅𝖺𝗍𝖾𝗌𝗍 𝖺𝗇𝗂𝗆𝖾 𝗇𝖾𝗐𝗌... 𝖯𝗅𝖾𝖺𝗌𝖾 𝗐𝖺𝗂𝗍.")
    
    news = await get_ann_news()

    if not news:
        await x.edit_text("𝖤𝗋𝗋𝗈𝗋 𝖿𝖾𝗍𝖼𝗁𝗂𝗇𝗀 𝗇𝖾𝗐𝗌. 𝖯𝗅𝖾𝖺𝗌𝖾 𝗍𝗋𝗒 𝖺𝗀𝖺𝗂𝗇 𝗅𝖺𝗍𝖾𝗋.")
        return
    

    
    await x.edit_text(
        news,
        disable_web_page_preview=True
    )


async def get_ann_news():
    """Fetch news from Anime News Network"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(ANIME_NEWS_NETWORK) as resp:
                if resp.status != 200:
                    return None
                
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                
                news_items = soup.select("div.herald.box.news")
                if not news_items:
                    return None
                
                result = "**𝖫𝖺𝗍𝖾𝗌𝗍 𝖠𝗇𝗂𝗆𝖾 𝖭𝖾𝗐𝗌 𝖿𝗋𝗈𝗆 𝖠𝗇𝗂𝗆𝖾 𝖭𝖾𝗐𝗌 𝖭𝖾𝗍𝗐𝗈𝗋𝗄:**\n\n"
                
                # Get the top 5 news items
                for i, item in enumerate(news_items[:10], 1):
                    title_elem = item.select_one("h3 a")
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    link = "https://www.animenewsnetwork.com" + title_elem["href"]
                    
                    
                    result += f"**{i}. [{title}...]({link})**\n\n"
                
                return result
        except Exception as e:
            print(f"Error fetching ANN news: {e}")
            return None






__module__ = "𝖠𝗇𝗂𝗆𝖾 𝖭𝖾𝗐𝗌"


__help__ = """✧ `/𝖺𝗇𝗂𝗆𝖾𝗇𝖾𝗐𝗌`: 𝖦𝖾𝗍 𝗍𝗁𝖾 𝗅𝖺𝗍𝖾𝗌𝗍 𝖺𝗇𝗂𝗆𝖾 𝗇𝖾𝗐𝗌 𝖿𝗋𝗈𝗆 𝖠𝗇𝗂𝗆𝖾 𝖭𝖾𝗐𝗌 𝖭𝖾𝗍𝗐𝗈𝗋𝗄.
""" 