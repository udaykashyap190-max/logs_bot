# =========================================================
# FILE: handlers/files.py
# PART 9H
# =========================================================

import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes
)

from core.auth import (
    has_access,
    is_admin
)

from core.process import (
    is_running
)

from database import (
    get_user_files
)


# =========================================================
# MY FILES
# =========================================================

async def my_files(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    user = update.effective_user


    if not user:

        return


    if not is_admin(user.id):

        if not has_access(user.id):

            return


    files = get_user_files(

        user.id

    )


    # =====================================================
    # NO FILES
    # =====================================================

    if not files:

        keyboard = [

            [

                InlineKeyboardButton(

                    "📤 Upload File",

                    callback_data="upload"

                )

            ],

            [

                InlineKeyboardButton(

                    "🔙 Back",

                    callback_data="home"

                )

            ]

        ]


        await update.message.reply_text(

            "📁 <b>MY FILES</b>\n\n"

            "You don't have any uploaded "
            "files yet.",

            parse_mode="HTML",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )

        return


    # =====================================================
    # FILE LIST
    # =====================================================

    keyboard = []


    for filename in files:

        running = is_running(

            user.id,

            filename

        )


        status = (

            "🟢"

            if running

            else

            "🔴"

        )


        keyboard.append(

            [

                InlineKeyboardButton(

                    f"{status} {filename}",

                    callback_data=
                    f"file|{filename}"

                )

            ]

        )


    keyboard.append(

        [

            InlineKeyboardButton(

                "📤 Upload File",

                callback_data="upload"

            )

        ]

    )


    keyboard.append(

        [

            InlineKeyboardButton(

                "🔙 Back",

                callback_data="home"

            )

        ]

    )


    await update.message.reply_text(

        "📁 <b>MY FILES</b>\n\n"

        "🟢 Running\n"
        "🔴 Stopped\n\n"

        "Select a file to manage it:",

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )

    )
