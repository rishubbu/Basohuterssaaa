import re
import math
from pyrogram import filters
from pyrogram.types import Message
from Yumeko import app
from config import config
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save

# Define safe mathematical functions
SAFE_FUNCTIONS = {
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'sqrt': math.sqrt,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'abs': abs,
    'ceil': math.ceil,
    'floor': math.floor,
    'round': round,
    'degrees': math.degrees,
    'radians': math.radians,
    'pi': math.pi,
    'e': math.e
}

def safe_eval(expr):
    """Safely evaluate a mathematical expression"""
    
    # Replace ^ with ** for exponentiation
    expr = expr.replace('^', '**')
    
    # Replace function names with safe versions
    for func_name in SAFE_FUNCTIONS:
        if isinstance(SAFE_FUNCTIONS[func_name], (int, float)):
            # Handle constants like pi and e
            expr = re.sub(r'\b' + func_name + r'\b', str(SAFE_FUNCTIONS[func_name]), expr)
        else:
            # Handle functions
            expr = re.sub(r'\b' + func_name + r'\(', 'SAFE_FUNCTIONS["' + func_name + '"](', expr)
    
    # Check for unsafe operations (case-insensitive)
    expr_lower = expr.lower()
    unsafe_ops = ['import', 'exec', 'eval', 'open', '__']
    if any(op in expr_lower for op in unsafe_ops):
        raise ValueError("Unsafe operation detected")
    
    # Only allow basic mathematical operations, digits, and letters
    allowed_chars = set('0123456789.+-*/()[] \t\n\r,abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"\'_')
    if not all(c in allowed_chars for c in expr):
        raise ValueError("Invalid characters in expression")
    
    # Evaluate the expression
    return eval(expr, {"__builtins__": {}}, {"SAFE_FUNCTIONS": SAFE_FUNCTIONS})

@app.on_message(filters.command(["calculate", "calc"], config.COMMAND_PREFIXES))
@error
@save
async def calculate_command(_, message: Message):
    """Calculate the result of a mathematical expression"""
    
    if len(message.command) < 2:
        await message.reply_text(
            "Please provide a mathematical expression to calculate.\n\n"
            "**Usage:** `/calculate [expression]` or `/calc [expression]`\n\n"
            "**Examples:**\n"
            "- `/calculate 2 + 2`\n"
            "- `/calc (5 + 3) * 2`\n"
            "- `/calc sin(30)`\n"
            "- `/calc sqrt(16)`"
        )
        return
    
    expression = message.text.split(None, 1)[1].strip()
    
    try:
        result = safe_eval(expression)
        
        if isinstance(result, (int, float)):
            if isinstance(result, int):
                formatted_result = f"{result:,}"
            else:
                if result.is_integer():
                    formatted_result = f"{int(result):,}"
                else:
                    formatted_result = f"{result:,.6f}".rstrip('0').rstrip('.')
        else:
            formatted_result = str(result)
        
        await message.reply_text(
            f"**Expression:** `{expression}`\n\n"
            f"**Result:** `{formatted_result}`"
        )
    
    except Exception as e:
        error_message = str(e)
        
        if "division by zero" in error_message.lower():
            error_message = "Division by zero is not allowed"
        elif "invalid syntax" in error_message.lower():
            error_message = "Invalid syntax in the expression"
        elif "unsafe operation" in error_message.lower() or "invalid characters" in error_message.lower():
            error_message = "Only basic mathematical operations and functions are allowed"
        elif "math domain error" in error_message.lower():
            error_message = "Math domain error (e.g., sqrt of negative number)"
        elif "name" in error_message.lower() and "is not defined" in error_message.lower():
            error_message = "Invalid function or variable name used"
        
        await message.reply_text(
            f"**Error:** {error_message}\n\n"
            "Please check your expression and try again."
        )


__module__ = "𝖢𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝗈𝗋"
__help__ = """
𝖯𝖾𝗋𝖿𝗈𝗋𝗆 𝗆𝖺𝗍𝗁𝖾𝗆𝖺𝗍𝗂𝖼𝖺𝗅 𝖼𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝗂𝗈𝗇𝗌.
 
**𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌:**
- /𝖼𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝖾 [𝖾𝗑𝗉𝗋𝖾𝗌𝗌𝗂𝗈𝗇]: 𝖢𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝖾 𝗍𝗁𝖾 𝗋𝖾𝗌𝗎𝗅𝗍 𝗈𝖿 𝖺 𝗆𝖺𝗍𝗁𝖾𝗆𝖺𝗍𝗂𝖼𝖺𝗅 𝖾𝗑𝗉𝗋𝖾𝗌𝗌𝗂𝗈𝗇
- /𝖼𝖺𝗅𝖼 [𝖾𝗑𝗉𝗋𝖾𝗌𝗌𝗂𝗈𝗇]: 𝖲𝗁𝗈𝗋𝗍𝗁𝖺𝗇𝖽 𝖿𝗈𝗋 /𝖼𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝖾

**𝖤𝗑𝖺𝗆𝗉𝗅𝖾𝗌:**
- `/𝖼𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝖾 𝟤 + 𝟤`
- `/𝖼𝖺𝗅𝖼 (𝟧 + 𝟥) * 𝟤`
- `/𝖼𝖺𝗅𝖼 𝗌𝗂𝗇(𝟥𝟢)`
- `/𝖼𝖺𝗅𝖼 𝗌𝗊𝗋𝗍(𝟣𝟨)`
"""
