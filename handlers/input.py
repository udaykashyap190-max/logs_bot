# =========================================================
# FILE: handlers/input.py
# PART 9F
# User-Specific Input Handler
# =========================================================

from telegram import Update
from telegram.ext import ContextTypes

from core.auth import (
    has_access,
    is_admin
)

from core.process import (
    send_input,
    is_running
)


# =========================================================
# HANDLE INPUT
# =========================================================

async def handle_input(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    user = update.effective_user

    message = update.message


    if not user or not message:

        return


    if not message.text:

        return


    user_id = user.id


    # =====================================================
    # ACCESS
    # =====================================================

    if not is_admin(
        user_id
    ):

        if not has_access(
            user_id
        ):

            return


    # =====================================================
    # ACTIVE FILE
    # =====================================================

    filename = context.user_data.get(

        "active_file"

    )


    if not filename:

        await message.reply_text(

            "⌨️ <b>No file selected</b>\n\n"

            "Open <b>My Files</b> and select "
            "the file that is waiting for input.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # RUNNING CHECK
    # =====================================================

    if not is_running(

        user_id,

        filename

    ):

        context.user_data.pop(

            "active_file",

            None

        )


        await message.reply_text(

            "❌ <b>Process is not running.</b>\n\n"

            f"📄 File: "
            f"<code>{filename}</code>",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # SEND INPUT
    # =====================================================

    success, result = send_input(

        user_id,

        filename,

        message.text

    )


    if success:

        await message.reply_text(

            "✅ <b>Input Sent</b>\n\n"

            f"📄 File: "
            f"<code>{filename}</code>\n"

            f"📤 Input: "
            f"<code>{message.text}</code>",

            parse_mode="HTML"

        )

        return


    await message.reply_text(

        f"❌ <b>Input Failed</b>\n\n"

        f"{result}",

        parse_mode="HTML"

    )
