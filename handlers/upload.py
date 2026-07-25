import os

from telegram import Update

from telegram.ext import ContextTypes

from core.auth import has_access

from handlers.callback import main_keyboard


UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


async def upload_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    message = update.message


    if user is None or message is None:

        return


    # =========================
    # CHECK USER ACCESS
    # =========================

    if not has_access(
        user.id
    ):

        await message.reply_text(

            "🚫 You don't have permission "
            "to use the file runner.\n\n"

            "Please ask the administrator "
            "to approve your account."

        )

        return


    # =========================
    # GET DOCUMENT
    # =========================

    document = message.document


    if document is None:

        return


    filename = document.file_name


    if not filename:

        await message.reply_text(

            "❌ Could not determine "
            "the file name."

        )

        return


    # =========================
    # CHECK PYTHON FILE
    # =========================

    if not filename.lower().endswith(
        ".py"
    ):

        await message.reply_text(

            "❌ Only Python (.py) files "
            "are supported."

        )

        return


    # =========================
    # DOWNLOAD FILE
    # =========================

    filepath = os.path.join(

        UPLOAD_FOLDER,

        filename

    )


    try:

        telegram_file = await document.get_file()


        await telegram_file.download_to_drive(

            filepath

        )


    except Exception as e:

        await message.reply_text(

            "❌ Failed to upload file.\n\n"

            f"Error: {e}"

        )

        return


    # =========================
    # SAVE ACTIVE FILE
    # =========================

    context.user_data[
        "active_file"
    ] = filename


    # =========================
    # SEND CONTROL BUTTONS
    # =========================

    await message.reply_text(

        f"✅ File uploaded successfully!\n\n"

        f"📄 File: `{filename}`\n\n"

        f"Choose an action:",

        parse_mode="Markdown",

        reply_markup=main_keyboard(

            filename

        )

    )