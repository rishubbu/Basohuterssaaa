import os
import shutil
import zipfile
import tarfile
import rarfile
from pyrogram import filters
from pyrogram.types import Message
from Yumeko import app
from config import config
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save



@app.on_message(filters.command("extract", config.COMMAND_PREFIXES))
@error
@save
async def extract_archive(_, message: Message):
    """Extract contents from archive files"""
    
    # Check if the message is a reply to a file
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text(
            "Please reply to an archive file (zip, tar, rar) to extract its contents.\n\n"
            "**Usage:** `/extract` (as a reply to an archive file)"
        )
        return
    
    # Get the file
    doc = message.reply_to_message.document
    file_name = doc.file_name
    
    # Check if the file is an archive
    if not file_name.endswith(('.zip', '.tar', '.tar.gz', '.tgz', '.rar')):
        await message.reply_text(
            "This doesn't seem to be an archive file. Supported formats: zip, tar, tar.gz, tgz, rar"
        )
        return
    
    # Send a processing message
    processing_msg = await message.reply_text("Downloading file...")
    
    try:
        # Create a temporary directory for extraction
        temp_dir = os.path.join(config.DOWNLOAD_LOCATION, f"extract_{message.from_user.id}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download the file
        file_path = os.path.join(temp_dir, file_name)
        await message.reply_to_message.download(file_path)
        
        await processing_msg.edit_text("Extracting contents...")
        
        # Extract based on file type
        extracted_files = []
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        
        if file_name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
                extracted_files = zip_ref.namelist()
        
        elif file_name.endswith(('.tar', '.tar.gz', '.tgz')):
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_path)
                extracted_files = tar_ref.getnames()
        
        elif file_name.endswith('.rar'):
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_path)
                extracted_files = rar_ref.namelist()
        
        # List extracted files (limit to 20 to avoid message too long)
        file_list = "\n".join([f"- `{f}`" for f in extracted_files[:20]])
        if len(extracted_files) > 20:
            file_list += f"\n\n...and {len(extracted_files) - 20} more files"
        
        # Send up to 10 extracted files
        sent_files = 0
        for root, _, files in os.walk(extract_path):
            for file in files:
                if sent_files >= 10:
                    break
                    
                file_path = os.path.join(root, file)
                try:
                    # Only send files smaller than 50MB
                    if os.path.getsize(file_path) < 50 * 1024 * 1024:
                        await message.reply_document(
                            file_path,
                            caption=f"Extracted: `{file}`"
                        )
                        sent_files += 1
                except Exception as e:
                    continue
        
        # Send summary
        await processing_msg.edit_text(
            f"**Extracted {len(extracted_files)} files from `{file_name}`**\n\n"
            f"**Sample of extracted files:**\n{file_list}\n\n"
            f"Sent {sent_files} files. Maximum 10 files can be sent."
        )
        
        # Clean up
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        await processing_msg.edit_text(
            f"An error occurred during extraction: {str(e)}"
        )
        # Clean up on error
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir) 

__module__ = "𝖤𝗑𝗍𝗋𝖺𝖼𝗍"
__help__ = """
𝖤𝗑𝗍𝗋𝖺𝖼𝗍 𝖼𝗈𝗇𝗍𝖾𝗇𝗍𝗌 𝖿𝗋𝗈𝗆 𝖺𝗋𝖼𝗁𝗂𝗏𝖾 𝖿𝗂𝗅𝖾𝗌.
 
**𝖢𝗈𝗆𝗆𝖺𝗇𝖽𝗌:**
- /𝖾𝗑𝗍𝗋𝖺𝖼𝗍 [𝗋𝖾𝗉𝗅𝗒 𝗍𝗈 𝖿𝗂𝗅𝖾]: 𝖤𝗑𝗍𝗋𝖺𝖼𝗍 𝖼𝗈𝗇𝗍𝖾𝗇𝗍𝗌 𝖿𝗋𝗈𝗆 𝗓𝗂𝗉, 𝗍𝖺𝗋, 𝗈𝗋 𝗋𝖺𝗋 𝖺𝗋𝖼𝗁𝗂𝗏𝖾𝗌
"""