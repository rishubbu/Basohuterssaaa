import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
from pyrogram import filters
from pyrogram.types import Message
from Yumeko import app
from config import config
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save
import shutil


# Language codes for OCR
OCR_LANGUAGES = {
    "eng": "English",
    "ara": "Arabic",
    "bul": "Bulgarian",
    "chs": "Chinese Simplified",
    "cht": "Chinese Traditional",
    "hrv": "Croatian",
    "cze": "Czech",
    "dan": "Danish",
    "dut": "Dutch",
    "fin": "Finnish",
    "fre": "French",
    "ger": "German",
    "gre": "Greek",
    "heb": "Hebrew",
    "hin": "Hindi",
    "hun": "Hungarian",
    "ind": "Indonesian",
    "ita": "Italian",
    "jpn": "Japanese",
    "kor": "Korean",
    "lav": "Latvian",
    "lit": "Lithuanian",
    "nor": "Norwegian",
    "pol": "Polish",
    "por": "Portuguese",
    "rum": "Romanian",
    "rus": "Russian",
    "srp": "Serbian",
    "slk": "Slovak",
    "slv": "Slovenian",
    "spa": "Spanish",
    "swe": "Swedish",
    "tha": "Thai",
    "tur": "Turkish",
    "ukr": "Ukrainian",
    "vie": "Vietnamese"
}

@app.on_message(filters.command("ocr", config.COMMAND_PREFIXES))
@error
@save
async def ocr_command(_, message: Message):
    """Extract text from images using OCR"""
    
    # Check if the message is a reply to an image
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text(
            "Please reply to an image to extract text.\n\n"
            "**Usage:** `/ocr` (as a reply to an image)\n"
            "**Usage with language:** `/ocr [language code]` (as a reply to an image)\n\n"
            "Available language codes: eng (English), spa (Spanish), fre (French), ger (German), etc."
        )
        return
    
    # Check if a language code is provided
    lang_code = "eng"  # Default to English
    if len(message.command) > 1:
        user_lang_code = message.command[1].lower()
        if user_lang_code in OCR_LANGUAGES:
            lang_code = user_lang_code
        else:
            await message.reply_text(
                f"Invalid language code: `{user_lang_code}`\n"
                "Using English (eng) as the default language.\n\n"
                "Available language codes: " + ", ".join([f"`{code}`" for code in OCR_LANGUAGES.keys()])
            )
    
    # Send a processing message
    processing_msg = await message.reply_text(f"Extracting text from image using {OCR_LANGUAGES.get(lang_code, 'Unknown')} language...")
    
    # Create a temporary directory for the image
    temp_dir = os.path.join(config.DOWNLOAD_LOCATION, f"ocr_{message.from_user.id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    image_path = None
    preprocessed_path = None
    
    try:
        # Download the image
        image_path = await message.reply_to_message.download(temp_dir)
        
        # Check if the downloaded path is a directory instead of a file
        if os.path.isdir(image_path):
            # Try to find the image file in the directory
            files = os.listdir(image_path)
            
            if files:
                # Use the first file in the directory
                image_path = os.path.join(image_path, files[0])
            else:
                raise ValueError(f"No files found in the downloaded directory: {image_path}")
        
        # Verify the image file exists
        if not os.path.isfile(image_path):
            raise ValueError(f"Downloaded path is not a valid file: {image_path}")
        
        # Open the image with PIL
        image = Image.open(image_path)
        
        # Preprocess the image for better OCR results
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get a binary image
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Save the preprocessed image
        preprocessed_path = os.path.join(temp_dir, "preprocessed.png")
        cv2.imwrite(preprocessed_path, binary)
        
        # Perform OCR on both original and preprocessed images
        text_original = pytesseract.image_to_string(image, lang=lang_code)
        text_preprocessed = pytesseract.image_to_string(Image.open(preprocessed_path), lang=lang_code)
        
        # Use the result with more text
        if len(text_preprocessed) > len(text_original):
            extracted_text = text_preprocessed
        else:
            extracted_text = text_original
        
        # Clean up the text
        extracted_text = extracted_text.strip()
        
        # Check if any text was extracted
        if not extracted_text:
            await processing_msg.edit_text(
                "No text could be extracted from this image. Try with a clearer image or a different language."
            )
            return
        
        # Format the response message
        response = (
            f"**Extracted Text ({OCR_LANGUAGES.get(lang_code, 'Unknown')}):**\n\n"
            f"`{extracted_text}`"
        )
        
        await processing_msg.edit_text(response)
    
    except Exception as e:
        await processing_msg.edit_text(
            f"An error occurred during OCR: {str(e)}"
        )
    
    finally:
        # Clean up files and directory safely
        try:
            
            # Remove temporary files if they exist
            if image_path and os.path.exists(image_path) and os.path.isfile(image_path):
                os.remove(image_path)
            elif image_path and os.path.exists(image_path) and os.path.isdir(image_path):
                shutil.rmtree(image_path, ignore_errors=True)
            
            if preprocessed_path and os.path.exists(preprocessed_path) and os.path.isfile(preprocessed_path):
                os.remove(preprocessed_path)
            
            # Remove the temporary directory safely
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")

__module__ = "𝖮𝖢𝖱"
__help__ = """
𝖤𝗑𝗍𝗋𝖺𝖼𝗍 𝗍𝖾𝗑𝗍 𝖿𝗋𝗈𝗆 𝗂𝗆𝖺𝗀𝖾𝗌 𝗎𝗌𝗂𝗇𝗀 𝖮𝗉𝗍𝗂𝖼𝖺𝗅 𝖢𝗁𝖺𝗋𝖺𝖼𝗍𝖾𝗋 𝖱𝖾𝖼𝗈𝗀𝗇𝗂𝗍𝗂𝗈𝗇 (𝖮𝖢𝖱).
 
**𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌:**
- /𝗈𝖼𝗋 [𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝗂𝗆𝖺𝗀𝖾]: 𝖤𝗑𝗍𝗋𝖺𝖼𝗍 𝗍𝖾𝗑𝗍 𝖿𝗋𝗈𝗆 𝖺𝗇 𝗂𝗆𝖺𝗀𝖾
- /𝗈𝖼𝗋 [𝗅𝖺𝗇𝗀𝗎𝖺𝗀𝖾 𝖼𝗈𝖽𝖾] [𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝗂𝗆𝖺𝗀𝖾]: 𝖤𝗑𝗍𝗋𝖺𝖼𝗍 𝗍𝖾𝗑𝗍 𝗂𝗇 𝖺 𝗌𝗉𝖾𝖼𝗂𝖿𝗂𝖼 𝗅𝖺𝗇𝗀𝗎𝖺𝗀𝖾
"""