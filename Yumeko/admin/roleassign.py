import json
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from Yumeko import app as pgram
from config import config
from Yumeko.decorator.errors import error
from Yumeko.decorator.save import save

OWNER_ID = config.OWNER_ID

# Path to the sudoers.json file
sudoers_file = "sudoers.json"

# Ensure the JSON file exists
if not os.path.exists(sudoers_file):
    with open(sudoers_file, "w") as f:
        json.dump({"Hokages": [], "Jonins": [], "Chunins": [], "Genins": []}, f, indent=4)

# Function to load roles from the file
def load_roles():
    with open(sudoers_file, "r") as f:
        return json.load(f)

# Function to save roles to the file
def save_roles(data):
    with open(sudoers_file, "w") as f:
        json.dump(data, f, indent=4)

# Ensure OWNER_ID is in Hokages
def ensure_owner_is_hokage():
    roles = load_roles()
    if OWNER_ID not in roles["Hokages"]:
        roles["Hokages"].append(OWNER_ID)
        save_roles(roles)

# Check if user has sufficient permissions
def has_permission(user_id):
    roles = load_roles()
    return user_id == OWNER_ID or user_id in roles["Hokages"] or user_id in roles["Jonins"] or user_id in roles["Chunins"]

# Command to assign roles
@pgram.on_message(filters.command("assign", prefixes=config.COMMAND_PREFIXES))
@error
@save
async def assign_role(client: Client, message: Message):
    ensure_owner_is_hokage()
    if not has_permission(message.from_user.id):
        await message.reply("You don't have permission to use this command.")
        return

    user_id = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) == 2 and message.command[1].isdigit():
        user_id = int(message.command[1])
    else:
        await message.reply("Please provide a valid UserID or reply to a user's message.")
        return

    roles = load_roles()
    allowed_roles_for_user = []
    if message.from_user.id == OWNER_ID:
        allowed_roles_for_user = ["Hokage", "Jonin", "Chunin", "Genin"]
    else:
        if message.from_user.id in roles["Hokages"]:
            allowed_roles_for_user = ["Jonin", "Chunin", "Genin"]
        elif message.from_user.id in roles["Jonins"]:
            allowed_roles_for_user = ["Chunin", "Genin"]
        elif message.from_user.id in roles["Chunins"]:
            allowed_roles_for_user = ["Genin"]
        else:
            allowed_roles_for_user = []

    if not allowed_roles_for_user:
        await message.reply("You don't have permission to assign any roles.")
        return

    role_buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(role, callback_data=f"assign:{role}:{user_id}:{message.from_user.id}")]
            for role in allowed_roles_for_user
        ]
    )
    await message.reply(
        "Choose a role to assign:",
        reply_markup=role_buttons
    )

# Callback handler for role assignment
@pgram.on_callback_query(filters.regex(r"^assign:(.+?):(\d+):(\d+)$"))
@error
@save
async def handle_assign_callback(client: Client, callback: CallbackQuery):
    ensure_owner_is_hokage()
    role, user_id, cmd_user_id = callback.data.split(":")[1:]
    user_id, cmd_user_id = int(user_id), int(cmd_user_id)

    if callback.from_user.id != cmd_user_id:
        await callback.answer("You are not allowed to perform this action.", show_alert=True)
        return

    roles = load_roles()
    valid_roles = ["Hokage", "Jonin", "Chunin", "Genin"]

    # Determine allowed roles based on the assigner's role
    allowed_roles = []
    if cmd_user_id == OWNER_ID:
        allowed_roles = valid_roles
    elif cmd_user_id in roles["Hokages"]:
        allowed_roles = valid_roles[1:]  # Exclude Hokage
    elif cmd_user_id in roles["Jonins"]:
        allowed_roles = valid_roles[2:]  # Only Chunin and Genin
    elif cmd_user_id in roles["Chunins"]:
        allowed_roles = valid_roles[3:]  # Only Genin
    else:
        await callback.answer("You don't have permission to assign roles.", show_alert=True)
        return

    if role not in allowed_roles:
        await callback.answer("You cannot assign this role.", show_alert=True)
        return

    # Remove the user from all roles first
    for r in valid_roles:
        list_name = f"{r}s" if r != "Genin" else "Genins"
        if user_id in roles[list_name]:
            roles[list_name].remove(user_id)

    # Assign the new role
    role_list = f"{role}s" if role != "Genin" else "Genins"
    roles[role_list].append(user_id)
    save_roles(roles)
    y = None
    try :
        x = await client.get_users(user_id)
        y = x.mention
    except Exception :
        x = user_id
        y = "None"

    await callback.edit_message_text(f"**Assigned {role} to user ID: {y} ({user_id})**")

# Command to remove users from their roles
@pgram.on_message(filters.command("unassign", prefixes=config.COMMAND_PREFIXES))
@error
@save
async def remove_role(client: Client, message: Message):
    ensure_owner_is_hokage()

    if not has_permission(message.from_user.id):
        await message.reply("You don't have permission to use this command.")
        return

    user_id = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) == 2 and message.command[1].isdigit():
        user_id = int(message.command[1])
    else:
        await message.reply("Please provide a valid UserID or reply to a user's message.")
        return

    roles = load_roles()
    removed = False

    # Remove the user from all roles
    for r in ["Hokages", "Jonins", "Chunins", "Genins"]:
        if user_id in roles[r]:
            roles[r].remove(user_id)
            removed = True

    if removed:
        save_roles(roles)
        await message.reply(f"**Removed all roles from user ID: {user_id}**")
    else:
        await message.reply(f"**User ID: {user_id} does not have any roles.**")

# Command to list all users with roles
@pgram.on_message(filters.command("staffs", prefixes=config.COMMAND_PREFIXES) & filters.user(OWNER_ID))
@error
@save
async def list_staffs(client: Client, message: Message):
    roles = load_roles()
    response = "**List of Staff:**\n\n"

    for role, users in roles.items():
        if users:
            response += f"**{role}:**\n"
            response += "\n".join([f"- `{user_id}`" for user_id in users])
            response += "\n\n"
        else:
            response += f"**{role}:** None\n\n"

    await message.reply(response)