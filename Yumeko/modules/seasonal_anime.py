import aiohttp
import datetime
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Yumeko import app
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save
from config import config

BOT_USERNAME = config.BOT_USERNAME

# Jikan API endpoints
JIKAN_SEASONAL = "https://api.jikan.moe/v4/seasons/"
JIKAN_SEASONS = "https://api.jikan.moe/v4/seasons"

# Get current season and year
def get_current_season():
    month = datetime.datetime.now().month
    if month in [1, 2, 3]:
        season = "winter"
    elif month in [4, 5, 6]:
        season = "spring"
    elif month in [7, 8, 9]:
        season = "summer"
    else:
        season = "fall"
    
    year = datetime.datetime.now().year
    return season, year

@app.on_message(filters.command("seasonal" , prefixes=config.COMMAND_PREFIXES))
@error
@save
async def seasonal_anime(client: Client, message: Message):
    """Get anime for a specific season"""
    text = message.text.split(" ", 2)
    
    # Default to current season
    current_season, current_year = get_current_season()
    season = current_season
    year = current_year
    
    if len(text) > 1:
        # Check if season is specified
        if text[1].lower() in ["winter", "spring", "summer", "fall"]:
            season = text[1].lower()
            
            # Check if year is also specified
            if len(text) > 2 and text[2].isdigit() and 1990 <= int(text[2]) <= current_year + 1:
                year = int(text[2])
        # Check if it's a special keyword
        elif text[1].lower() == "upcoming":
            # Get next season
            seasons = ["winter", "spring", "summer", "fall"]
            current_idx = seasons.index(current_season)
            next_idx = (current_idx + 1) % 4
            season = seasons[next_idx]
            year = current_year if next_idx > current_idx else current_year + 1
        elif text[1].lower() == "previous":
            # Get previous season
            seasons = ["winter", "spring", "summer", "fall"]
            current_idx = seasons.index(current_season)
            prev_idx = (current_idx - 1) % 4
            season = seasons[prev_idx]
            year = current_year if prev_idx < current_idx else current_year - 1
    
    x = await message.reply_text(f"𝖥𝖾𝗍𝖼𝗁𝗂𝗇𝗀 𝖺𝗇𝗂𝗆𝖾 𝖿𝗈𝗋 {season.capitalize()} {year}... 𝖯𝗅𝖾𝖺𝗌𝖾 𝗐𝖺𝗂𝗍.")
    
    anime_list = await get_seasonal_anime(season, year)
    
    if not anime_list:
        await x.edit_text("𝖤𝗋𝗋𝗈𝗋 𝖿𝖾𝗍𝖼𝗁𝗂𝗇𝗀 𝗌𝖾𝖺𝗌𝗈𝗇𝖺𝗅 𝖺𝗇𝗂𝗆𝖾. 𝖯𝗅𝖾𝖺𝗌𝖾 𝗍𝗋𝗒 𝖺𝗀𝖺𝗂𝗇 𝗅𝖺𝗍𝖾𝗋.")
        return
    
    # Create buttons for navigation
    seasons = ["winter", "spring", "summer", "fall"]
    current_idx = seasons.index(season)
    next_idx = (current_idx + 1) % 4
    prev_idx = (current_idx - 1) % 4
    
    next_season = seasons[next_idx]
    prev_season = seasons[prev_idx]
    
    next_year = year if next_idx > current_idx else year + 1
    prev_year = year if prev_idx < current_idx else year - 1
    
    buttons = [
        [
            InlineKeyboardButton(
                f"◀️ {prev_season.capitalize()} {prev_year}",
                callback_data=f"season_{prev_season}_{prev_year}_{message.from_user.id}"
            ),
            InlineKeyboardButton(
                f"{next_season.capitalize()} {next_year} ▶️",
                callback_data=f"season_{next_season}_{next_year}_{message.from_user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Current Season",
                callback_data=f"season_{current_season}_{current_year}_{message.from_user.id}"
            )
        ]
    ]
    await x.delete()
    await message.reply_text(
        anime_list,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


@app.on_message(filters.command("seasons" , prefixes=config.COMMAND_PREFIXES))
@error
@save
async def available_seasons(client: Client, message: Message):
    """Get list of available seasons"""
    x = await message.reply_text("𝖥𝖾𝗍𝖼𝗁𝗂𝗇𝗀 𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝗌𝖾𝖺𝗌𝗈𝗇𝗌... 𝖯𝗅𝖾𝖺𝗌𝖾 𝗐𝖺𝗂𝗍.")
    
    seasons_list = await get_available_seasons()
    
    if not seasons_list:
        await x.edit_text("𝖤𝗋𝗋𝗈𝗋 𝖿𝖾𝗍𝖼𝗁𝗂𝗇𝗀 𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝗌𝖾𝖺𝗌𝗈𝗇𝗌. 𝖯𝗅𝖾𝖺𝗌𝖾 𝗍𝗋𝗒 𝖺𝗀𝖺𝗂𝗇 𝗅𝖺𝗍𝖾𝗋.")
        return
    
    await x.delete()
    await message.reply_text(seasons_list)


async def get_seasonal_anime(season, year):
    """Fetch seasonal anime from Jikan API"""
    url = f"{JIKAN_SEASONAL}{year}/{season}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                anime_data = data.get("data", [])
                
                if not anime_data:
                    return f"𝖭𝗈 𝖺𝗇𝗂𝗆𝖾 𝖿𝗈𝗎𝗇𝖽 𝖿𝗈𝗋 {season.capitalize()} {year}."
                
                # Sort by popularity (members count)
                anime_data.sort(key=lambda x: x.get("members", 0), reverse=True)
                
                result = f"**𝖳𝗈𝗉 𝖠𝗇𝗂𝗆𝖾 𝖿𝗈𝗋 {season.capitalize()} {year}:**\n\n"
                
                # Get the top 15 anime
                for i, anime in enumerate(anime_data[:15], 1):
                    title = anime.get("title")
                    url = anime.get("url")
                    score = anime.get("score", "N/A")
                    type_ = anime.get("type", "Unknown")
                    episodes = anime.get("episodes", "?")
                    
                    result += f"**{i}. [{title}]({url})**\n"
                    result += f"📊 Score: {score} | 📺 Type: {type_} | 🎬 Episodes: {episodes}\n\n"
                
                return result
        except Exception as e:
            print(f"Error fetching seasonal anime: {e}")
            return None


async def get_available_seasons():
    """Fetch available seasons from Jikan API"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(JIKAN_SEASONS) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                seasons_data = data.get("data", [])
                
                if not seasons_data:
                    return "𝖭𝗈 𝗌𝖾𝖺𝗌𝗈𝗇𝗌 𝖿𝗈𝗎𝗇𝖽."
                
                result = "**𝖠𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝖲𝖾𝖺𝗌𝗈𝗇𝗌:**\n\n"
                
                # Group by year
                years = {}
                for season in seasons_data:
                    year = season.get("year")
                    season_name = season.get("season")
                    
                    if year not in years:
                        years[year] = []
                    
                    years[year].append(season_name.capitalize())
                
                # Sort years in descending order
                for year in sorted(years.keys(), reverse=True):
                    result += f"**{year}:** {', '.join(years[year])}\n"
                
                result += "\n𝖳𝗈 𝗏𝗂𝖾𝗐 𝖺 𝗌𝗉𝖾𝖼𝗂𝖿𝗂𝖼 𝗌𝖾𝖺𝗌𝗈𝗇, 𝗎𝗌𝖾 `/𝗌𝖾𝖺𝗌𝗈𝗇𝖺𝗅 [𝗌𝖾𝖺𝗌𝗈𝗇] [𝗒𝖾𝖺𝗋]`\n𝖤𝗑𝖺𝗆𝗉𝗅𝖾: `/𝗌𝖾𝖺𝗌𝗈𝗇𝖺𝗅 𝗐𝗂𝗇𝗍𝖾𝗋 2023`"
                
                return result
        except Exception as e:
            print(f"Error fetching available seasons: {e}")
            return None


@app.on_callback_query(filters.regex(pattern=r"season_(.*)_(.*)_(.*)"))
async def season_callback(client, callback_query):
    """Handle season navigation callbacks"""
    season, year, user_id = callback_query.data.split("_")[1:]
    
    # Check if the user who clicked is the same who requested
    if int(user_id) != callback_query.from_user.id:
        await callback_query.answer("This is not for you!", show_alert=True)
        return
    
    await callback_query.answer(f"Fetching anime for {season.capitalize()} {year}...")
    
    anime_list = await get_seasonal_anime(season, year)
    
    if not anime_list:
        await callback_query.answer("Error fetching seasonal anime. Please try again later.", show_alert=True)
        return
    
    # Get current season for the "Current Season" button
    current_season, current_year = get_current_season()
    
    # Create buttons for navigation
    seasons = ["winter", "spring", "summer", "fall"]
    current_idx = seasons.index(season)
    next_idx = (current_idx + 1) % 4
    prev_idx = (current_idx - 1) % 4
    
    next_season = seasons[next_idx]
    prev_season = seasons[prev_idx]
    
    year = int(year)
    next_year = year if next_idx > current_idx else year + 1
    prev_year = year if prev_idx < current_idx else year - 1
    
    buttons = [
        [
            InlineKeyboardButton(
                f"◀️ {prev_season.capitalize()} {prev_year}",
                callback_data=f"season_{prev_season}_{prev_year}_{user_id}"
            ),
            InlineKeyboardButton(
                f"{next_season.capitalize()} {next_year} ▶️",
                callback_data=f"season_{next_season}_{next_year}_{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Current Season",
                callback_data=f"season_{current_season}_{current_year}_{user_id}"
            )
        ]
    ]
    
    await callback_query.edit_message_text(
        anime_list,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


__module__ = "𝖲𝖾𝖺𝗌𝗈𝗇𝖺𝗅 𝖠𝗇𝗂𝗆𝖾"


__help__ = """✧ `/𝗌𝖾𝖺𝗌𝗈𝗇𝖺𝗅`: 𝖦𝖾𝗍 𝖺𝗇𝗂𝗆𝖾 𝖿𝗈𝗋 𝗍𝗁𝖾 𝖼𝗎𝗋𝗋𝖾𝗇𝗍 𝗌𝖾𝖺𝗌𝗈𝗇.
✧ `/𝗌𝖾𝖺𝗌𝗈𝗇𝖺𝗅 [𝗌𝖾𝖺𝗌𝗈𝗇] [𝗒𝖾𝖺𝗋]`: 𝖦𝖾𝗍 𝖺𝗇𝗂𝗆𝖾 𝖿𝗈𝗋 𝖺 𝗌𝗉𝖾𝖼𝗂𝖿𝗂𝖼 𝗌𝖾𝖺𝗌𝗈𝗇 𝖺𝗇𝖽 𝗒𝖾𝖺𝗋.
✧ `/𝗌𝖾𝖺𝗌𝗈𝗇𝖺𝗅 𝗎𝗉𝖼𝗈𝗆𝗂𝗇𝗀`: 𝖦𝖾𝗍 𝖺𝗇𝗂𝗆𝖾 𝖿𝗈𝗋 𝗍𝗁𝖾 𝗎𝗉𝖼𝗈𝗆𝗂𝗇𝗀 𝗌𝖾𝖺𝗌𝗈𝗇.
✧ `/𝗌𝖾𝖺𝗌𝗈𝗇𝖺𝗅 𝗉𝗋𝖾𝗏𝗂𝗈𝗎𝗌`: 𝖦𝖾𝗍 𝖺𝗇𝗂𝗆𝖾 𝖿𝗈𝗋 𝗍𝗁𝖾 𝗉𝗋𝖾𝗏𝗂𝗈𝗎𝗌 𝗌𝖾𝖺𝗌𝗈𝗇.
✧ `/𝗌𝖾𝖺𝗌𝗈𝗇𝗌`: 𝖦𝖾𝗍 𝖺 𝗅𝗂𝗌𝗍 𝗈𝖿 𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝗌𝖾𝖺𝗌𝗈𝗇𝗌.

𝖲𝖾𝖺𝗌𝗈𝗇𝗌: 𝗐𝗂𝗇𝗍𝖾𝗋, 𝗌𝗉𝗋𝗂𝗇𝗀, 𝗌𝗎𝗆𝗆𝖾𝗋, 𝖿𝖺𝗅𝗅
""" 