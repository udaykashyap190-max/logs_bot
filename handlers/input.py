# =========================================================
# FILE: handlers/input.py
# PART 9E
# Interactive Input Handler
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
# HANDLE USER INPUT
# =========================================================

async def handle_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if user is None:
        return


    message = update.message

    if message is None:
        return


    text = message.text

    if not text:
        return


    user_id = user.id


    # =====================================================
    # ACCESS CHECK
    # =====================================================

    if not is_admin(user_id):

        if not has_access(user_id):

            return


    # =====================================================
    # GET SELECTED FILE
    # =====================================================

    filename = context.user_data.get(
        "active_file"
    )


    # =====================================================
    # NO FILE SELECTED
    # =====================================================

    if not filename:

        await message.reply_text(

            "ℹ️ <b>No file selected for input.</b>\n\n"

            "Open your uploaded files and press "
            "⌨️ <b>Send Input</b> on the file that "
            "is asking for information.\n\n"

            "For example:\n"
            "• API Key\n"
            "• Chat ID\n"
            "• Username\n"
            "• Password\n"
            "• Any other input",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # CHECK PROCESS
    # =====================================================

    if not is_running(
        filename
    ):

        # Clear invalid active file

        context.user_data.pop(
            "active_file",
            None
        )


        await message.reply_text(

            f"❌ <b>{filename}</b> "
            "is no longer running.\n\n"

            "Please start the file again "
            "and select ⌨️ <b>Send Input</b>.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # SEND INPUT
    # =====================================================

    success, result = send_input(

        filename,

        text

    )


    # =====================================================
    # SUCCESS
    # =====================================================

    if success:

        await message.reply_text(

            "✅ <b>Input Sent</b>\n\n"

            f"📄 File: "
            f"<code>{filename}</code>\n"

            f"📤 Input: "
            f"<code>{text}</code>",

            parse_mode="HTML"

        )


        # Keep active_file selected.
        # This allows the user to answer
        # multiple questions from the same file.

        return


    # =====================================================
    # FAILED
    # =====================================================

    await message.reply_text(

        f"❌ <b>Input Failed</b>\n\n"
        f"{result}",

        parse_mode="HTML"

    )
