# =========================================================
# FILE: handlers/callback.py
# PART 9G
# My Files + Process Controls
# =========================================================

import os

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from core.auth import (
    has_access,
    is_admin
)

from core.process import (
    start_process,
    stop_process,
    restart_process,
    get_logs,
    clear_logs,
    is_running,
    get_user_upload_folder
)

# =========================================================
# MY FILES MENU
# =========================================================

async def show_my_files(

    query,

    user_id

):

    folder = get_user_upload_folder(

        user_id

    )


    try:

        files = sorted(

            [

                f

                for f in os.listdir(
                    folder
                )

                if f.lower().endswith(
                    ".py"
                )

            ]

        )

    except Exception:

        files = []


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

            ]

        ]


        await query.edit_message_text(

            "📂 <b>MY FILES</b>\n\n"

            "You haven't uploaded any Python "
            "files yet.",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            ),

            parse_mode="HTML"

        )

        return


    # =====================================================
    # FILE BUTTONS
    # =====================================================

    keyboard = []


    for filename in files:

        running = is_running(

            user_id,

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

                "🔄 Refresh",

                callback_data="my_files"

            )

        ]

    )


    await query.edit_message_text(

        "📂 <b>MY FILES</b>\n\n"

        "🟢 Running\n"
        "🔴 Stopped\n\n"

        "Select a file to manage it:",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="HTML"

    )

# =========================================================
# FILE CONTROL MENU
# =========================================================

async def show_file_controls(

    query,

    user_id,

    filename

):

    running = is_running(

        user_id,

        filename

    )


    status = (

        "🟢 RUNNING"

        if running

        else

        "🔴 STOPPED"

    )


    keyboard = []


    if running:

        keyboard.append(

            [

                InlineKeyboardButton(

                    "⏹️ Stop",

                    callback_data=
                    f"stop|{filename}"

                ),

                InlineKeyboardButton(

                    "🔄 Restart",

                    callback_data=
                    f"restart|{filename}"

                )

            ]

        )

    else:

        keyboard.append(

            [

                InlineKeyboardButton(

                    "▶️ Start",

                    callback_data=
                    f"start|{filename}"

                )

            ]

        )


    keyboard.append(

        [

            InlineKeyboardButton(

                "📜 Logs",

                callback_data=
                f"logs|{filename}"

            ),

            InlineKeyboardButton(

                "⌨️ Input",

                callback_data=
                f"input|{filename}"

            )

        ]

    )


    keyboard.append(

        [

            InlineKeyboardButton(

                "🧹 Clear Logs",

                callback_data=
                f"clear_logs|{filename}"

            )

        ]

    )


    keyboard.append(

        [

            InlineKeyboardButton(

                "⬅️ My Files",

                callback_data="my_files"

            )

        ]

    )


    await query.edit_message_text(

        "📄 <b>FILE CONTROL</b>\n\n"

        f"📁 <code>{filename}</code>\n\n"

        f"Status: <b>{status}</b>\n\n"

        "Choose an action:",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="HTML"

    )
