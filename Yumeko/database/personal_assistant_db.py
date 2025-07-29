from Yumeko.database import db
from datetime import datetime, timedelta


todo_collection = db.personal_assistant_todo
notes_collection = db.personal_assistant_notes
reminders_collection = db.personal_assistant_reminders

# ----- TO-DO LIST FUNCTIONS -----

async def add_todo_item(user_id, task_content):
    """Add a new task to the to-do list"""
    timestamp = datetime.now()
    
    result = await todo_collection.insert_one({
        "user_id": user_id,
        "task": task_content,
        "status": "pending",
        "created_at": timestamp,
        "updated_at": timestamp
    })
    
    return result.inserted_id

async def get_todos(user_id):
    """Get all tasks for a user"""
    cursor = todo_collection.find({"user_id": user_id}).sort("created_at", 1)
    return await cursor.to_list(length=None)

async def mark_todo_as_done(todo_id):
    """Mark a task as completed"""
    await todo_collection.update_one(
        {"_id": todo_id},
        {"$set": {"status": "completed", "updated_at": datetime.now()}}
    )

async def remove_todo_item(todo_id):
    """Remove a task from the to-do list"""
    await todo_collection.delete_one({"_id": todo_id})

async def clear_todos(user_id):
    """Clear all tasks for a user"""
    result = await todo_collection.delete_many({"user_id": user_id})
    return result.deleted_count

# ----- NOTES FUNCTIONS -----

async def add_note(user_id, title, content):
    """Add a new note"""
    timestamp = datetime.now()
    
    result = await notes_collection.insert_one({
        "user_id": user_id,
        "title": title,
        "content": content,
        "created_at": timestamp,
        "updated_at": timestamp
    })
    
    return result.inserted_id

async def get_notes(user_id):
    """Get all notes for a user"""
    cursor = notes_collection.find({"user_id": user_id}).sort("created_at", 1)
    return await cursor.to_list(length=None)

async def get_note_by_id(note_id):
    """Get a specific note by ID"""
    return await notes_collection.find_one({"_id": note_id})

async def update_note(note_id, title, content):
    """Update a note"""
    await notes_collection.update_one(
        {"_id": note_id},
        {
            "$set": {
                "title": title,
                "content": content,
                "updated_at": datetime.now()
            }
        }
    )

async def remove_note(note_id):
    """Remove a note"""
    await notes_collection.delete_one({"_id": note_id})

async def clear_notes(user_id):
    """Clear all notes for a user"""
    result = await notes_collection.delete_many({"user_id": user_id})
    return result.deleted_count

# ----- REMINDER FUNCTIONS -----

async def add_reminder(user_id, reminder_time, reminder_text):
    """Add a new reminder"""
    result = await reminders_collection.insert_one({
        "user_id": user_id,
        "reminder_text": reminder_text,
        "reminder_time": reminder_time,
        "created_at": datetime.now(),
        "status": "pending"
    })
    
    return str(result.inserted_id)

async def get_active_reminders(user_id):
    """Get all active reminders for a user"""
    cursor = reminders_collection.find({
        "user_id": user_id,
        "status": "pending",
        "reminder_time": {"$gt": datetime.now()}
    }).sort("reminder_time", 1)
    return await cursor.to_list(length=None)

async def mark_reminder_as_sent(reminder_id):
    """Mark a reminder as sent"""
    await reminders_collection.update_one(
        {"_id": reminder_id},
        {"$set": {"status": "sent"}}
    )

async def cancel_reminder(reminder_id):
    """Cancel a reminder"""
    await reminders_collection.update_one(
        {"_id": reminder_id},
        {"$set": {"status": "cancelled"}}
    )

async def clear_old_reminders():
    """Clear old reminders (older than 30 days)"""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    result = await reminders_collection.delete_many({
        "reminder_time": {"$lt": thirty_days_ago},
        "status": {"$in": ["sent", "cancelled"]}
    })
    return result.deleted_count 