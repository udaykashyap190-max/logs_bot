from telegram import Update

from telegram.ext import (
    ContextTypes
)

from core.auth import is_owner

from core.process import (
    send_input,
    is_running
)


async def handle_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user is None:

        return


    if not is_owner(
        user.id
    ):

        return


    message = update.message


    if message is None:

        return


    text = message.text


    if not text:

        return


    filename = context.user_data.get(
        "active_file"
    )


    if not filename:

        await message.reply_text(

            "ℹ️ No file is selected "
            "for input.\n\n"

            "Click ⌨️ Send Input on "
            "the file you want to control."

        )

        return


    if not is_running(
        filename
    ):

        await message.reply_text(

            f"❌ `{filename}` is not running.",

            parse_mode="Markdown"

        )

        return


    success, result = send_input(

        filename,

        text

    )


    if success:

        await message.reply_text(

            f"✅ Input sent to `{filename}`.",

            parse_mode="Markdown"

        )

    else:

        await message.reply_text(

            result

        )