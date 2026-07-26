# =========================================================
# FILE: handlers/upload.py
# PART 9H
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

from database import (
    add_file_owner,
    create_process_record
)


# =========================================================
# UPLOAD FILE
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
    # ACCESS
    # =====================================================

    if not is_admin(user_id):

        if not has_access(user_id):

            await message.reply_text(

                "🚫 You don't have permission "
                "to use this bot."

            )

            return


    # =====================================================
    # DOCUMENT
    # =====================================================

    document = message.document


    if not document:

        return


    filename = document.file_name


    if not filename:

        await message.reply_text(

            "❌ Could not detect file name."

        )

        return


    filename = os.path.basename(

        filename

    )


    # =====================================================
    # PYTHON CHECK
    # =====================================================

    if not filename.lower().endswith(

        ".py"

    ):

        await message.reply_text(

            "❌ <b>Invalid File</b>\n\n"

            "Only Python <code>.py</code> "
            "files are supported.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # USER FOLDER
    # =====================================================

    folder = get_user_upload_folder(

        user_id

    )


    filepath = os.path.join(

        folder,

        filename

    )


    # =====================================================
    # DOWNLOAD
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
    # DATABASE REGISTRATION
    # =====================================================

    add_file_owner(

        user_id,

        filename

    )


    create_process_record(

        user_id,

        filename

    )


    # =====================================================
    # SUCCESS
    # =====================================================

    await message.reply_text(

        "✅ <b>File Uploaded Successfully</b>\n\n"

        f"📄 <b>File:</b> "
        f"<code>{filename}</code>\n\n"

        "📂 Open <b>My Files</b> to manage it.",

        parse_mode="HTML"

    )
