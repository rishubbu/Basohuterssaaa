from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Yumeko import app, scheduler
from Yumeko.database import db
from Yumeko.database.personal_assistant_db import (
    add_todo_item, get_todos, mark_todo_as_done, remove_todo_item, clear_todos,
    add_note, get_notes, get_note_by_id, update_note, remove_note, clear_notes,
    add_reminder, get_active_reminders, mark_reminder_as_sent, cancel_reminder as cancel_reminder_db
)
from config import config
from Yumeko.decorator.save import save
from Yumeko.decorator.errors import error
from datetime import datetime, timedelta
import re
from bson import ObjectId


# --------- TO-DO LIST FUNCTIONS ---------

@app.on_message(filters.command("todo", prefixes=config.COMMAND_PREFIXES) & filters.private)
@error
@save
async def todo_handler(client: Client, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split(maxsplit=2)
    
    if len(command_parts) == 1:
        # If just /todo, show help
        await message.reply_text(
            "**📝 To-Do List Commands:**\n"
            "• `/todo add <task>` - Add a task\n"
            "• `/todo list` - View your to-do list\n"
            "• `/todo done <task_id>` - Mark as done\n"
            "• `/todo remove <task_id>` - Remove a task\n"
            "• `/todo clear` - Clear your list"
        )
        return
    
    action = command_parts[1].lower()
    
    if action == "add" and len(command_parts) > 2:
        task_content = command_parts[2]
        await add_todo(client, message, user_id, task_content)
    
    elif action == "list":
        await list_todos(client, message, user_id)
    
    elif action == "done" and len(command_parts) > 2:
        try:
            task_id = int(command_parts[2])
            await mark_todo_done(client, message, user_id, task_id)
        except ValueError:
            await message.reply_text("❌ Please provide a valid task ID number.")
    
    elif action == "remove" and len(command_parts) > 2:
        try:
            task_id = int(command_parts[2])
            await remove_todo(client, message, user_id, task_id)
        except ValueError:
            await message.reply_text("❌ Please provide a valid task ID number.")
    
    elif action == "clear":
        await clear_todos_confirmation(client, message, user_id)
    
    else:
        await message.reply_text("❌ Invalid command format. Use `/todo add <task>`, `/todo list`, etc.")

async def add_todo(client, message, user_id, task_content):
    # Insert the new task using the async function from personal_assistant_db
    await add_todo_item(user_id, task_content)
    
    await message.reply_text(f"✅ Task added to your to-do list:\n**{task_content}**")

async def list_todos(client, message, user_id):
    # Get all tasks for the user using the async function
    tasks = await get_todos(user_id)
    
    if not tasks:
        await message.reply_text("📝 Your to-do list is empty.")
        return
    
    # Format the tasks
    task_list = "📋 **Your To-Do List:**\n\n"
    for i, task in enumerate(tasks, 1):
        status = "✅" if task["status"] == "completed" else "⬜️"
        task_list += f"{i}. {status} {task['task']}\n"
    
    # Add a delete button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ Delete", callback_data="delete")]
    ])
    
    await message.reply_text(task_list, reply_markup=keyboard)

async def mark_todo_done(client, message, user_id, task_id):
    # Get all tasks for the user using the async function
    tasks = await get_todos(user_id)
    
    if not tasks:
        await message.reply_text("📝 Your to-do list is empty.")
        return
    
    if task_id < 1 or task_id > len(tasks):
        await message.reply_text(f"❌ Invalid task ID. You have {len(tasks)} tasks.")
        return
    
    # Get the task and update its status using the async function
    task = tasks[task_id - 1]
    await mark_todo_as_done(task["_id"])
    
    await message.reply_text(f"✅ Marked task as done:\n**{task['task']}**")

async def remove_todo(client, message, user_id, task_id):
    # Get all tasks for the user using the async function
    tasks = await get_todos(user_id)
    
    if not tasks:
        await message.reply_text("📝 Your to-do list is empty.")
        return
    
    if task_id < 1 or task_id > len(tasks):
        await message.reply_text(f"❌ Invalid task ID. You have {len(tasks)} tasks.")
        return
    
    # Get the task and delete it using the async function
    task = tasks[task_id - 1]
    await remove_todo_item(task["_id"])
    
    await message.reply_text(f"🗑️ Removed task from your list:\n**{task['task']}**")

async def clear_todos_confirmation(client, message, user_id):
    # Create confirmation buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"todo_clear_confirm_{user_id}"),
            InlineKeyboardButton("❌ No", callback_data="delete")
        ]
    ])
    
    await message.reply_text(
        "⚠️ **Are you sure you want to clear your entire to-do list?**\n"
        "This action cannot be undone.",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^todo_clear_confirm_(\d+)$"))
async def todo_clear_confirm(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    
    # Verify the user is the same who initiated the command
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This action was not initiated by you.", show_alert=True)
        return
    
    # Delete all tasks for the user using the async function
    deleted_count = await clear_todos(user_id)
    
    await callback_query.message.edit_text(
        f"🗑️ Your to-do list has been cleared. {deleted_count} tasks removed."
    )

# --------- NOTES FUNCTIONS ---------

@app.on_message(filters.command("note", prefixes=config.COMMAND_PREFIXES) & filters.private)
@error
@save
async def note_handler(client: Client, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split(maxsplit=2)
    
    if len(command_parts) == 1:
        # If just /note, show help
        await message.reply_text(
            "**📝 Notes Commands:**\n"
            "• `/note add <title> <content>` - Add a new note\n"
            "• `/note list` - List all your saved notes\n"
            "• `/note view <note_id>` - View a specific note\n"
            "• `/note remove <note_id>` - Remove a note\n"
            "• `/note clear` - Clear all your notes"
        )
        return
    
    action = command_parts[1].lower()
    
    if action == "add" and len(command_parts) > 2:
        content = command_parts[2]
        # Extract title and content
        match = re.match(r"([^\n]+)\n([\s\S]+)", content)
        
        if match:
            title = match.group(1).strip()
            note_content = match.group(2).strip()
        else:
            # If no newline, use the first few words as title
            parts = content.split(maxsplit=3)
            if len(parts) >= 4:
                title = " ".join(parts[:3])
                note_content = parts[3]
            else:
                title = "Untitled Note"
                note_content = content
        
        await add_note_handler(client, message, user_id, title, note_content)
    
    elif action == "list":
        await list_notes_handler(client, message, user_id)
    
    elif action == "view" and len(command_parts) > 2:
        try:
            note_id = int(command_parts[2])
            await view_note_handler(client, message, user_id, note_id)
        except ValueError:
            await message.reply_text("❌ Please provide a valid note ID number.")
    
    elif action == "remove" and len(command_parts) > 2:
        try:
            note_id = int(command_parts[2])
            await remove_note_handler(client, message, user_id, note_id)
        except ValueError:
            await message.reply_text("❌ Please provide a valid note ID number.")
    
    elif action == "clear":
        await clear_notes_handler(client, message, user_id)
    
    else:
        await message.reply_text("❌ Invalid command format. Use `/note add <title> <content>`, `/note list`, etc.")

async def add_note_handler(client, message, user_id, title, content):
    # Insert the new note using the async function
    await add_note(user_id, title, content)
    
    await message.reply_text(f"📝 Note saved successfully!\n**Title:** {title}")

async def list_notes_handler(client, message, user_id):
    # Get all notes for the user using the async function
    notes = await get_notes(user_id)
    
    if not notes:
        await message.reply_text("📝 You don't have any saved notes.")
        return
    
    # Format the notes
    note_list = "📋 **Your Notes:**\n\n"
    for i, note in enumerate(notes, 1):
        created_date = note["created_at"].strftime("%Y-%m-%d")
        note_list += f"{i}. **{note['title']}** - {created_date}\n"
    
    note_list += "\nUse `/note view <number>` to view a specific note."
    
    # Add a delete button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ Delete", callback_data="delete")]
    ])
    
    await message.reply_text(note_list, reply_markup=keyboard)

async def view_note_handler(client, message, user_id, note_id):
    # Get all notes for the user using the async function
    notes = await get_notes(user_id)
    
    if not notes:
        await message.reply_text("📝 You don't have any saved notes.")
        return
    
    if note_id < 1 or note_id > len(notes):
        await message.reply_text(f"❌ Invalid note ID. You have {len(notes)} notes.")
        return
    
    # Get the note
    note = notes[note_id - 1]
    created_date = note["created_at"].strftime("%Y-%m-%d %H:%M")
    
    # Create buttons for the note
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗑️ Delete Note", callback_data=f"note_delete_{note['_id']}")
        ],
        [
            InlineKeyboardButton("🔙 Back to List", callback_data=f"note_list_{user_id}")
        ]
    ])
    
    await message.reply_text(
        f"📝 **{note['title']}**\n"
        f"📅 {created_date}\n\n"
        f"{note['content']}",
        reply_markup=keyboard
    )

async def remove_note_handler(client, message, user_id, note_id):
    # Get all notes for the user using the async function
    notes = await get_notes(user_id)
    
    if not notes:
        await message.reply_text("📝 You don't have any saved notes.")
        return
    
    if note_id < 1 or note_id > len(notes):
        await message.reply_text(f"❌ Invalid note ID. You have {len(notes)} notes.")
        return
    
    # Get the note and delete it using the async function
    note = notes[note_id - 1]
    await remove_note(note["_id"])
    
    await message.reply_text(f"🗑️ Note deleted: **{note['title']}**")

async def clear_notes_handler(client, message, user_id):
    # Create confirmation buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"notes_clear_confirm_{user_id}"),
            InlineKeyboardButton("❌ No", callback_data="delete")
        ]
    ])
    
    await message.reply_text(
        "⚠️ **Are you sure you want to delete all your notes?**\n"
        "This action cannot be undone.",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"^notes_clear_confirm_(\d+)$"))
async def notes_clear_confirm(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    
    # Verify the user is the same who initiated the command
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This action was not initiated by you.", show_alert=True)
        return
    
    # Delete all notes for the user using the async function
    deleted_count = await clear_notes(user_id)
    
    await callback_query.message.edit_text(
        f"🗑️ All your notes have been deleted. {deleted_count} notes removed."
    )

@app.on_callback_query(filters.regex(r"^note_list_(\d+)$"))
async def note_list_callback(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    
    # Verify the user is the same who initiated the command
    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ This action was not initiated by you.", show_alert=True)
        return
    
    # Get all notes for the user using the async function
    notes = await get_notes(user_id)
    
    if not notes:
        await callback_query.message.edit_text("📝 You don't have any saved notes.")
        return
    
    # Format the notes
    note_list = "📋 **Your Notes:**\n\n"
    for i, note in enumerate(notes, 1):
        created_date = note["created_at"].strftime("%Y-%m-%d")
        note_list += f"{i}. **{note['title']}** - {created_date}\n"
    
    note_list += "\nUse `/note view <number>` to view a specific note."
    
    # Add a delete button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ Delete", callback_data="delete")]
    ])
    
    await callback_query.message.edit_text(note_list, reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^note_delete_(.+)$"))
async def note_delete_callback(client: Client, callback_query: CallbackQuery):
    note_id_str = callback_query.data.split("_")[-1]
    
    try:
        # Convert string to ObjectId
        note_id = ObjectId(note_id_str)
        
        # Get the note using the async function
        note = await get_note_by_id(note_id)
        
        if not note:
            await callback_query.answer("❌ Note not found.", show_alert=True)
            return
        
        # Verify the user is the same who owns the note
        if callback_query.from_user.id != note["user_id"]:
            await callback_query.answer("❌ This note doesn't belong to you.", show_alert=True)
            return
        
        # Delete the note using the async function
        await remove_note(note_id)
        
        await callback_query.message.edit_text(f"🗑️ Note deleted: **{note['title']}**")
        
    except Exception as e:
        await callback_query.answer(f"❌ Error: {str(e)}", show_alert=True)

# --------- REMINDER FUNCTIONS ---------

@app.on_message(filters.command("remind", prefixes=config.COMMAND_PREFIXES) & filters.private)
@error
@save
async def remind_handler(client: Client, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split(maxsplit=2)
    
    if len(command_parts) < 3:
        await message.reply_text(
            "❌ Please provide both time and message.\n"
            "Examples:\n"
            "• `/remind 30m Call mom`\n"
            "• `/remind 2h Finish homework`\n"
            "• `/remind tomorrow 9am Meeting`"
        )
        return
    
    time_str = command_parts[1].lower()
    reminder_text = command_parts[2]
    
    # Parse the time
    try:
        reminder_time = parse_time(time_str)
        if not reminder_time:
            await message.reply_text(
                "❌ Invalid time format. Examples:\n"
                "• `30m` - 30 minutes from now\n"
                "• `2h` - 2 hours from now\n"
                "• `tomorrow 9am` - tomorrow at 9 AM"
            )
            return
    except Exception as e:
        await message.reply_text(f"❌ Error parsing time: {str(e)}")
        return
    
    # Store the reminder using the async function
    reminder_id = await add_reminder(user_id, reminder_time, reminder_text)
    
    # Schedule the reminder
    scheduler.add_job(
        send_reminder,
        'date',
        run_date=reminder_time,
        args=[client, user_id, reminder_text, reminder_id],
        id=f"reminder_{reminder_id}"
    )
    
    # Format the time for display
    time_diff = reminder_time - datetime.now()
    if time_diff.days > 0:
        time_display = f"{time_diff.days} days, {time_diff.seconds // 3600} hours"
    elif time_diff.seconds >= 3600:
        time_display = f"{time_diff.seconds // 3600} hours, {(time_diff.seconds % 3600) // 60} minutes"
    else:
        time_display = f"{time_diff.seconds // 60} minutes"
    
    await message.reply_text(
        f"⏰ Reminder set!\n"
        f"I'll remind you about: **{reminder_text}**\n"
        f"Time: {reminder_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"(in {time_display})"
    )

def parse_time(time_str):
    now = datetime.now()
    
    # Simple formats: 30m, 2h, etc.
    if re.match(r'^\d+[mh]$', time_str):
        value = int(time_str[:-1])
        unit = time_str[-1]
        
        if unit == 'm':
            return now + timedelta(minutes=value)
        elif unit == 'h':
            return now + timedelta(hours=value)
    
    # Format: tomorrow 9am
    elif 'tomorrow' in time_str:
        tomorrow = now + timedelta(days=1)
        time_part = time_str.replace('tomorrow', '').strip()
        
        # Parse time like 9am, 10pm, etc.
        match = re.match(r'(\d+)(am|pm)', time_part)
        if match:
            hour = int(match.group(1))
            ampm = match.group(2)
            
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            return tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    # Format: today 9pm
    elif 'today' in time_str:
        time_part = time_str.replace('today', '').strip()
        
        # Parse time like 9am, 10pm, etc.
        match = re.match(r'(\d+)(am|pm)', time_part)
        if match:
            hour = int(match.group(1))
            ampm = match.group(2)
            
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            return now.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    return None

async def send_reminder(client, user_id, reminder_text, reminder_id):
    try:
        # Send the reminder message
        await client.send_message(
            user_id,
            f"⏰ **REMINDER**\n\n{reminder_text}"
        )
        
        # Update the reminder status using the async function
        await mark_reminder_as_sent(ObjectId(reminder_id))
    except Exception as e:
        print(f"Error sending reminder: {e}")

@app.on_message(filters.command("reminders", prefixes=config.COMMAND_PREFIXES) & filters.private)
@error
@save
async def list_reminders(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Get all pending reminders for the user using the async function
    reminders = await get_active_reminders(user_id)
    
    if not reminders:
        await message.reply_text("⏰ You don't have any active reminders.")
        return
    
    # Format the reminders
    reminder_list = "⏰ **Your Active Reminders:**\n\n"
    for i, reminder in enumerate(reminders, 1):
        reminder_time = reminder["reminder_time"].strftime("%Y-%m-%d %H:%M")
        reminder_list += f"{i}. **{reminder_time}**\n{reminder['reminder_text']}\n\n"
    
    # Add a delete button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑️ Delete", callback_data="delete")]
    ])
    
    await message.reply_text(reminder_list, reply_markup=keyboard)

@app.on_message(filters.command("cancel_reminder", prefixes=config.COMMAND_PREFIXES) & filters.private)
@error
@save
async def cancel_reminder_handler(client: Client, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) < 2:
        await message.reply_text("❌ Please provide the reminder ID to cancel.")
        return
    
    try:
        reminder_index = int(command_parts[1])
        
        # Get all pending reminders for the user using the async function
        reminders = await get_active_reminders(user_id)
        
        if not reminders:
            await message.reply_text("⏰ You don't have any active reminders.")
            return
        
        if reminder_index < 1 or reminder_index > len(reminders):
            await message.reply_text(f"❌ Invalid reminder ID. You have {len(reminders)} active reminders.")
            return
        
        # Get the reminder and cancel it
        reminder = reminders[reminder_index - 1]
        reminder_id = reminder["_id"]
        
        # Remove from scheduler
        try:
            scheduler.remove_job(f"reminder_{str(reminder_id)}")
        except:
            pass
        
        # Update in database using the async function
        await cancel_reminder_db(reminder_id)
        
        await message.reply_text(f"✅ Reminder cancelled: **{reminder['reminder_text']}**")
        
    except ValueError:
        await message.reply_text("❌ Please provide a valid reminder ID number.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")


__module__ = "𝖯𝖾𝗋𝗌𝗈𝗇𝖺𝗅 𝖠𝗌𝗌𝗂𝗌𝗍𝖺𝗇𝗍"
__help__ = """
**Personal Assistant Features**

**To-Do List Commands:**
• `/todo add <task>` - Add a task to your to-do list
• `/todo list` - View your to-do list
• `/todo done <task_id>` - Mark a task as done
• `/todo remove <task_id>` - Remove a task from your list
• `/todo clear` - Clear your entire to-do list

**Notes Commands:**
• `/note add <title> <content>` - Add a new note
• `/note list` - List all your saved notes
• `/note view <note_id>` - View a specific note
• `/note remove <note_id>` - Remove a note
• `/note clear` - Clear all your notes

**Reminder Commands:**
• `/remind <time> <message>` - Set a reminder
  Examples: 
  - `/remind 30m Call mom`
  - `/remind 2h Finish homework`
  - `/remind tomorrow 9am Meeting`
• `/reminders` - List all your active reminders
• `/cancel_reminder <reminder_id>` - Cancel a specific reminder
"""