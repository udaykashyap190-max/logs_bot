from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ContextTypes
)

from core.auth import (
    register_user,
    get_status,
    has_access,
    is_admin
)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if user is None:

        return


    # Register user
    register_user(
        user
    )


    status = get_status(
        user.id
    )


    # =========================
    # ADMIN
    # =========================

    if is_admin(
        user.id
    ):

        keyboard = [

            [

                InlineKeyboardButton(
                    "👑 Admin Panel",
                    callback_data="admin_panel"
                )

            ]

        ]


        await update.message.reply_text(

            "👑 Welcome, Admin!\n\n"

            "You have full access to the "
            "file runner.",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )

        return


    # =========================
    # APPROVED USER
    # =========================

    if has_access(
        user.id
    ):

        await update.message.reply_text(

            "✅ Access Approved!\n\n"

            "You can now use the file runner.\n\n"

            "📤 Send me a Python (.py) file "
            "to upload."

        )

        return


    # =========================
    # PENDING
    # =========================

    if status == "pending":

        await update.message.reply_text(

            "⏳ Access Pending\n\n"

            "Your access request has been "
            "sent to the administrator.\n\n"

            "Please wait until your request "
            "is approved."

        )

        return


    # =========================
    # BLOCKED
    # =========================

    if status == "blocked":

        await update.message.reply_text(

            "🚫 Access Denied\n\n"

            "You currently don't have permission "
            "to use this bot."

        )

        return