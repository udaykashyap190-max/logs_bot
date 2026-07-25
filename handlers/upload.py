import os

from telegram import Update

from telegram.ext import (
    ContextTypes
)

from core.auth import has_access

from database import add_file_owner


UPLOAD_FOLDER = "uploads"


async def upload_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    if not has_access(user.id):

        await update.message.reply_text(
            "🚫 You don't have permission "
            "to upload files."
        )

        return

    document = update.message.document

    if not document:

        return

    filename = document.file_name

    if not filename:

        await update.message.reply_text(
            "❌ Invalid filename."
        )

        return

    # Only Python files
    if not filename.lower().endswith(".py"):

        await update.message.reply_text(
            "❌ Only Python (.py) files "
            "are allowed."
        )

        return

    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True
    )

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    try:

        telegram_file = await document.get_file()

        await telegram_file.download_to_drive(
            filepath
        )

        # Save file ownership
        add_file_owner(
            user.id,
            filename
        )

        await update.message.reply_text(

            "✅ <b>FILE UPLOADED</b>\n\n"

            f"📄 <code>{filename}</code>\n\n"

            "Your file has been saved.\n"

            "Open 📁 <b>My Files</b> "
            "to manage it.",

            parse_mode="HTML"

        )

    except Exception as e:

        await update.message.reply_text(

            "❌ <b>UPLOAD FAILED</b>\n\n"

            f"<code>{str(e)}</code>",

            parse_mode="HTML"

        )
