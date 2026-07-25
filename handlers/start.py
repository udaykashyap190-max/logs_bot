from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from core.auth import has_access
from database import (
    save_user,
    get_user_status,
    get_user_file_count
)


def main_menu_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "📁 My Files",
                callback_data="my_files"
            ),

            InlineKeyboardButton(
                "📤 Upload File",
                callback_data="upload"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 My Statistics",
                callback_data="stats"
            ),

            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help"
            )
        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    # Save/update user
    save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    # Check access
    if not has_access(user.id):

        status = get_user_status(
            user.id
        )

        if status == "pending":

            text = (
                "⏳ <b>ACCESS REQUEST PENDING</b>\n\n"
                "Your access request has been sent "
                "to the administrator.\n\n"
                "Please wait for approval."
            )

        elif status == "rejected":

            text = (
                "🚫 <b>ACCESS DENIED</b>\n\n"
                "Your access request was rejected "
                "by the administrator."
            )

        else:

            text = (
                "🔐 <b>ACCESS REQUIRED</b>\n\n"
                "You don't have permission to use "
                "this bot yet.\n\n"
                "Please contact the administrator "
                "for access."
            )

        await update.message.reply_text(
            text,
            parse_mode="HTML"
        )

        return

    # File count
    file_count = get_user_file_count(
        user.id
    )

    # Main welcome
    text = (
        "╔════════════════════════════╗\n"
        "      🤖 <b>FILE RUNNER BOT</b>\n"
        "╚════════════════════════════╝\n\n"

        f"👋 Welcome, <b>{user.first_name}</b>!\n\n"

        "🚀 Upload and manage your Python files "
        "directly from Telegram.\n\n"

        f"📁 Your Files: <b>{file_count}</b>\n\n"

        "Choose an option below:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
