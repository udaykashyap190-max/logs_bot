# =========================================================
# FILE: handlers/callback.py
# PART 9G
# Complete Callback Handler
#
# Supports:
# - My Files
# - File selection
# - Start
# - Stop
# - Restart
# - Logs
# - Clear Logs
# - Send Input
# - Upload button
# =========================================================

import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ContextTypes
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
# ACCESS CHECK
# =========================================================

def user_has_access(user_id):

    if is_admin(user_id):

        return True

    return has_access(user_id)


# =========================================================
# MY FILES
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

                filename

                for filename in os.listdir(
                    folder
                )

                if filename.lower().endswith(
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

            ],

            [

                InlineKeyboardButton(

                    "⬅️ Back",

                    callback_data="home"

                )

            ]

        ]


        await query.edit_message_text(

            "📂 <b>MY FILES</b>\n\n"

            "You don't have any uploaded "
            "Python files yet.\n\n"

            "Upload a <code>.py</code> file to "
            "get started.",

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


    # =====================================================
    # BOTTOM BUTTONS
    # =====================================================

    keyboard.append(

        [

            InlineKeyboardButton(

                "🔄 Refresh",

                callback_data="my_files"

            ),

            InlineKeyboardButton(

                "📤 Upload",

                callback_data="upload"

            )

        ]

    )


    keyboard.append(

        [

            InlineKeyboardButton(

                "⬅️ Back",

                callback_data="home"

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


    if running:

        status = "🟢 RUNNING"

    else:

        status = "🔴 STOPPED"


    keyboard = []


    # =====================================================
    # START / STOP / RESTART
    # =====================================================

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


    # =====================================================
    # LOGS + INPUT
    # =====================================================

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


    # =====================================================
    # CLEAR LOGS
    # =====================================================

    keyboard.append(

        [

            InlineKeyboardButton(

                "🧹 Clear Logs",

                callback_data=
                f"clear_logs|{filename}"

            )

        ]

    )


    # =====================================================
    # BACK
    # =====================================================

    keyboard.append(

        [

            InlineKeyboardButton(

                "⬅️ My Files",

                callback_data="my_files"

            )

        ]

    )


    await query.edit_message_text(

        "📄 <b>FILE CONTROL PANEL</b>\n\n"

        f"📁 <b>File:</b> "
        f"<code>{filename}</code>\n\n"

        f"📊 <b>Status:</b> {status}\n\n"

        "Choose an action below:",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="HTML"

    )


# =========================================================
# CALLBACK HANDLER
# =========================================================

async def handle_callback(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    query = update.callback_query


    if not query:

        return


    await query.answer()


    user = query.from_user


    if not user:

        return


    user_id = user.id


    # =====================================================
    # ACCESS CHECK
    # =====================================================

    if not user_has_access(

        user_id

    ):

        await query.answer(

            "🚫 You don't have permission "
            "to use this bot.",

            show_alert=True

        )

        return


    data = query.data


    if not data:

        return


    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        keyboard = InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "📂 My Files",

                    callback_data="my_files"

                )

            ],

            [

                InlineKeyboardButton(

                    "📤 Upload File",

                    callback_data="upload"

                )

            ]

        ])


        await query.edit_message_text(

            "🤖 <b>PYTHON FILE MANAGER</b>\n\n"

            "Choose an option below:",

            reply_markup=keyboard,

            parse_mode="HTML"

        )

        return


    # =====================================================
    # MY FILES
    # =====================================================

    if data == "my_files":

        await show_my_files(

            query,

            user_id

        )

        return


    # =====================================================
    # UPLOAD
    # =====================================================

    if data == "upload":

        await query.message.reply_text(

            "📤 <b>UPLOAD FILE</b>\n\n"

            "Send me a Python file "
            "with the <code>.py</code> extension.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # FILE SELECTION
    # =====================================================

    if data.startswith(

        "file|"

    ):

        filename = data.split(

            "|",

            1

        )[1]


        # -------------------------------------------------
        # SECURITY CHECK
        # -------------------------------------------------

        filename = os.path.basename(

            filename

        )


        filepath = os.path.join(

            get_user_upload_folder(

                user_id

            ),

            filename

        )


        if not os.path.isfile(

            filepath

        ):

            await query.answer(

                "❌ File no longer exists.",

                show_alert=True

            )


            await show_my_files(

                query,

                user_id

            )

            return


        await show_file_controls(

            query,

            user_id,

            filename

        )

        return


    # =====================================================
    # SPLIT ACTION
    # =====================================================

    if "|" not in data:

        return


    action, filename = data.split(

        "|",

        1

    )


    # =====================================================
    # SECURITY
    # =====================================================

    filename = os.path.basename(

        filename

    )


    filepath = os.path.join(

        get_user_upload_folder(

            user_id

        ),

        filename

    )


    if not os.path.isfile(

        filepath

    ):

        await query.answer(

            "❌ File not found.",

            show_alert=True

        )

        return


    # =====================================================
    # START
    # =====================================================

    if action == "start":

        success, message = start_process(

            user_id,

            filename

        )


        if success:

            context.user_data[

                "active_file"

            ] = filename


        await query.answer(

            message,

            show_alert=True

        )


        await show_file_controls(

            query,

            user_id,

            filename

        )

        return


    # =====================================================
    # STOP
    # =====================================================

    if action == "stop":

        success, message = stop_process(

            user_id,

            filename

        )


        # -------------------------------------------------
        # CLEAR ACTIVE FILE IF STOPPED
        # -------------------------------------------------

        if (

            context.user_data.get(

                "active_file"

            )

            == filename

        ):

            context.user_data.pop(

                "active_file",

                None

            )


        await query.answer(

            message,

            show_alert=True

        )


        await show_file_controls(

            query,

            user_id,

            filename

        )

        return


    # =====================================================
    # RESTART
    # =====================================================

    if action == "restart":

        success, message = restart_process(

            user_id,

            filename

        )


        if success:

            context.user_data[

                "active_file"

            ] = filename


        await query.answer(

            message,

            show_alert=True

        )


        await show_file_controls(

            query,

            user_id,

            filename

        )

        return


    # =====================================================
    # LOGS
    # =====================================================

    if action == "logs":

        logs = get_logs(

            user_id,

            filename

        )


        # -------------------------------------------------
        # ESCAPE HTML
        # -------------------------------------------------

        logs = (

            logs

            .replace(

                "&",

                "&amp;"

            )

            .replace(

                "<",

                "&lt;"

            )

            .replace(

                ">",

                "&gt;"

            )

        )


        # -------------------------------------------------
        # TELEGRAM MESSAGE LIMIT
        # -------------------------------------------------

        if len(logs) > 3800:

            logs = (

                "… Showing latest logs …\n\n"

                + logs[
                    -3800:
                ]

            )


        await query.message.reply_text(

            "📜 <b>PROCESS LOGS</b>\n\n"

            f"📄 <b>File:</b> "
            f"<code>{filename}</code>\n\n"

            f"<pre>{logs}</pre>",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # CLEAR LOGS
    # =====================================================

    if action == "clear_logs":

        success = clear_logs(

            user_id,

            filename

        )


        if success:

            await query.answer(

                "🧹 Logs cleared successfully.",

                show_alert=True

            )

        else:

            await query.answer(

                "❌ Failed to clear logs.",

                show_alert=True

            )


        return


    # =====================================================
    # INPUT MODE
    # =====================================================

    if action == "input":

        if not is_running(

            user_id,

            filename

        ):

            await query.answer(

                "❌ This file is not running.",

                show_alert=True

            )

            return


        # -------------------------------------------------
        # SAVE ACTIVE FILE
        # -------------------------------------------------

        context.user_data[

            "active_file"

        ] = filename


        await query.message.reply_text(

            "⌨️ <b>INPUT MODE ENABLED</b>\n\n"

            f"📄 <b>File:</b> "
            f"<code>{filename}</code>\n\n"

            "The next normal text message you "
            "send will be passed to this running "
            "file.\n\n"

            "You can enter anything the program "
            "asks for, such as:\n"

            "• API Key\n"
            "• Chat ID\n"
            "• Username\n"
            "• Password\n"
            "• Number\n"
            "• Choice\n"
            "• Any other input\n\n"

            "⚠️ Make sure you selected the correct "
            "file before sending the input.",

            parse_mode="HTML"

        )

        return


# =========================================================
# END OF FILE
# =========================================================
