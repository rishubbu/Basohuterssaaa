import httpx
import json
import os
import time
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message
from Yumeko import app
from config import config
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save



# API endpoint for currency conversion
CURRENCY_API_URL = "https://api.exchangerate-api.com/v4/latest/"

# Cache file for exchange rates
CACHE_DIR = os.path.join(config.DOWNLOAD_LOCATION, "currency_cache")
CACHE_FILE = os.path.join(CACHE_DIR, "exchange_rates.json")

# Cache duration in seconds (1 day)
CACHE_DURATION = 86400

# Common currency codes
CURRENCY_CODES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "JPY": "Japanese Yen",
    "GBP": "British Pound",
    "AUD": "Australian Dollar",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "HKD": "Hong Kong Dollar",
    "NZD": "New Zealand Dollar",
    "SEK": "Swedish Krona",
    "KRW": "South Korean Won",
    "SGD": "Singapore Dollar",
    "NOK": "Norwegian Krone",
    "MXN": "Mexican Peso",
    "INR": "Indian Rupee",
    "RUB": "Russian Ruble",
    "ZAR": "South African Rand",
    "TRY": "Turkish Lira",
    "BRL": "Brazilian Real",
    "TWD": "Taiwan Dollar",
    "DKK": "Danish Krone",
    "PLN": "Polish Zloty",
    "THB": "Thai Baht",
    "IDR": "Indonesian Rupiah",
    "HUF": "Hungarian Forint",
    "CZK": "Czech Koruna",
    "ILS": "Israeli Shekel",
    "CLP": "Chilean Peso",
    "PHP": "Philippine Peso",
    "AED": "UAE Dirham",
    "COP": "Colombian Peso",
    "SAR": "Saudi Riyal",
    "MYR": "Malaysian Ringgit",
    "RON": "Romanian Leu"
}

async def get_exchange_rates(base_currency="USD"):
    """Get exchange rates from API or cache"""
    
    # Create cache directory if it doesn't exist
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Check if cache file exists and is not expired
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                
            # Check if cache is for the requested base currency
            if cache_data.get("base") == base_currency:
                # Check if cache is not expired
                cache_time = cache_data.get("timestamp", 0)
                if time.time() - cache_time < CACHE_DURATION:
                    return cache_data
        except Exception:
            # If there's any error reading the cache, ignore and fetch fresh data
            pass
    
    # Fetch fresh data from API
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CURRENCY_API_URL}{base_currency}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Add timestamp to data
            data["timestamp"] = time.time()
            
            # Save to cache
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f)
            
            return data
        
        raise Exception(f"API returned status code {response.status_code}")

@app.on_message(filters.command("currency", config.COMMAND_PREFIXES))
@error
@save
async def currency_command(_, message: Message):
    """Convert between different currencies"""
    
    # Check if it's a request for the currency list
    if len(message.command) == 2 and message.command[1].lower() == "list":
        # Format the currency list
        currency_list = "\n".join([f"**{code}**: {name}" for code, name in sorted(CURRENCY_CODES.items())])
        
        await message.reply_text(
            "**Available Currencies:**\n\n"
            f"{currency_list}"
        )
        return
    
    # Check if there are enough arguments
    if len(message.command) < 4:
        await message.reply_text(
            "Please provide the amount, source currency, and target currency.\n\n"
            "**Usage:** `/currency [amount] [from] [to]`\n\n"
            "**Examples:**\n"
            "- `/currency 100 USD EUR` - Convert 100 US Dollars to Euros\n"
            "- `/currency 50 JPY INR` - Convert 50 Japanese Yen to Indian Rupees\n\n"
            "Use `/currency list` to see available currencies."
        )
        return
    
    # Get the arguments
    try:
        amount = float(message.command[1])
        from_currency = message.command[2].upper()
        to_currency = message.command[3].upper()
    except ValueError:
        await message.reply_text(
            "Invalid amount. Please provide a valid number."
        )
        return
    
    # Send a processing message
    processing_msg = await message.reply_text(f"Converting {amount} {from_currency} to {to_currency}...")
    
    try:
        # Get exchange rates with the source currency as base
        rates_data = await get_exchange_rates(from_currency)
        
        # Check if the currencies are valid
        if from_currency != rates_data.get("base"):
            await processing_msg.edit_text(
                f"Invalid source currency: `{from_currency}`\n\n"
                "Use `/currency list` to see available currencies."
            )
            return
        
        rates = rates_data.get("rates", {})
        
        if to_currency not in rates:
            await processing_msg.edit_text(
                f"Invalid target currency: `{to_currency}`\n\n"
                "Use `/currency list` to see available currencies."
            )
            return
        
        # Calculate the converted amount
        converted_amount = amount * rates[to_currency]
        
        # Format the result
        from_currency_name = CURRENCY_CODES.get(from_currency, from_currency)
        to_currency_name = CURRENCY_CODES.get(to_currency, to_currency)
        
        # Get the last update time
        last_update = datetime.fromtimestamp(rates_data.get("timestamp", time.time()))
        last_update_str = last_update.strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the response message
        response = (
            f"**{amount:,.2f} {from_currency}** ({from_currency_name}) = \n"
            f"**{converted_amount:,.2f} {to_currency}** ({to_currency_name})\n\n"
            f"**Exchange Rate:** 1 {from_currency} = {rates[to_currency]:,.6f} {to_currency}\n"
            f"**Last Updated:** {last_update_str}"
        )
        
        await processing_msg.edit_text(response)
    
    except Exception as e:
        await processing_msg.edit_text(
            f"An error occurred: {str(e)}\n\n"
            "Please check your currencies and try again."
        ) 

__module__ = "𝖢𝗎𝗋𝗋𝖾𝗇𝖼𝗒"
__help__ = """
𝖢𝗈𝗇𝗏𝖾𝗋𝗍 𝖻𝖾𝗍𝗐𝖾𝖾𝗇 𝖽𝗂𝖿𝖿𝖾𝗋𝖾𝗇𝗍 𝖼𝗎𝗋𝗋𝖾𝗇𝖼𝗂𝖾𝗌.
 
**𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌:**
- /𝖼𝗎𝗋𝗋𝖾𝗇𝖼𝗒 [𝖺𝗆𝗈𝗎𝗇𝗍] [𝖿𝗋𝗈𝗆] [𝗍𝗈]: 𝖢𝗈𝗇𝗏𝖾𝗋𝗍 𝖼𝗎𝗋𝗋𝖾𝗇𝖼𝗒
- /𝖼𝗎𝗋𝗋𝖾𝗇𝖼𝗒 𝗅𝗂𝗌𝗍: 𝖲𝗁𝗈𝗐 𝖺𝗏𝖺𝗂𝗅𝖺𝖻𝗅𝖾 𝖼𝗎𝗋𝗋𝖾𝗇𝖼𝗂𝖾𝗌

**𝖤𝗑𝖺𝗆𝗉𝗅𝖾𝗌:**
- `/𝖼𝗎𝗋𝗋𝖾𝗇𝖼𝗒 𝟣𝟢𝟢 𝖴𝖲𝖣 𝖤𝖴𝖱` - 𝖢𝗈𝗇𝗏𝖾𝗋𝗍 𝟣𝟢𝟢 𝖴𝖲 𝖣𝗈𝗅𝗅𝖺𝗋𝗌 𝗍𝗈 𝖤𝗎𝗋𝗈𝗌
- `/𝖼𝗎𝗋𝗋𝖾𝗇𝖼𝗒 𝟧𝟢 𝖩𝖯𝖸 𝖨𝖭𝖱` - 𝖢𝗈𝗇𝗏𝖾𝗋𝗍 𝟧𝟢 𝖩𝖺𝗉𝖺𝗇𝖾𝗌𝖾 𝖸𝖾𝗇 𝗍𝗈 𝖨𝗇𝖽𝗂𝖺𝗇 𝖱𝗎𝗉𝖾𝖾𝗌
"""