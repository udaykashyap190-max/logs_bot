# =========================================================
# FILE: handlers/upload.py
# PART 9G
# User-Specific Python File Upload
# =========================================================

import os

from telegram import Update

from telegram.ext import (
    ContextTypes
)

from core.auth import (
    has_access,
    is_admin
)

from core.process import (
    get_user_upload_folder
)


# =========================================================
# HANDLE FILE UPLOAD
# =========================================================

async def upload_file(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    user = update.effective_user

    message = update.message


    if not user or not message:

        return


    user_id = user.id


    # =====================================================
    # ACCESS CHECK
    # =====================================================

    if not is_admin(
        user_id
    ):

        if not has_access(
            user_id
        ):

            await message.reply_text(

                "🚫 You don't have permission "
                "to use this bot."

            )

            return


    # =====================================================
    # CHECK DOCUMENT
    # =====================================================

    if not message.document:

        return


    document = message.document


    # =====================================================
    # FILE NAME
    # =====================================================

    filename = document.file_name


    if not filename:

        await message.reply_text(

            "❌ Could not detect file name."

        )

        return


    # =====================================================
    # PYTHON FILE ONLY
    # =====================================================

    if not filename.lower().endswith(
        ".py"
    ):

        await message.reply_text(

            "❌ <b>Invalid File</b>\n\n"

            "Only Python <code>.py</code> files "
            "are supported.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # USER UPLOAD DIRECTORY
    # =====================================================

    upload_folder = get_user_upload_folder(

        user_id

    )


    filepath = os.path.join(

        upload_folder,

        os.path.basename(
            filename
        )

    )


    # =====================================================
    # DOWNLOAD FILE
    # =====================================================

    try:

        telegram_file = await context.bot.get_file(

            document.file_id

        )


        await telegram_file.download_to_drive(

            filepath

        )


    except Exception as e:

        await message.reply_text(

            "❌ <b>Upload Failed</b>\n\n"

            f"<code>{e}</code>",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # SUCCESS
    # =====================================================

    await message.reply_text(

        "✅ <b>File Uploaded Successfully</b>\n\n"

        f"📄 File: "
        f"<code>{filename}</code>\n\n"

        "📂 Open <b>My Files</b> to manage it.",

        parse_mode="HTML"

    )
