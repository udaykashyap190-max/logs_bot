import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from core.auth import has_access

from core.process import (
    start_process,
    stop_process,
    restart_process,
    is_running,
    get_logs,
    clear_logs
)

from database import (
    get_user_files,
    user_owns_file,
    remove_user_file,
    get_user_file_count
)


UPLOAD_FOLDER = "uploads"


# =========================================================
# MAIN MENU
# =========================================================

def home_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "📁 My Files",
                callback_data="my_files"
            ),

            InlineKeyboardButton(
                "📤 Upload File",
                callback_data="upload"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="stats"
            ),

            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help"
            )
        ]

    ])


# =========================================================
# FILE LIST
# =========================================================

def files_keyboard(user_id):

    files = get_user_files(
        user_id
    )

    keyboard = []

    for filename in files:

        status = (
            "🟢"
            if is_running(filename)
            else "🔴"
        )

        keyboard.append([

            InlineKeyboardButton(
                f"{status} {filename}",
                callback_data=
                f"file|{filename}"
            )

        ])

    keyboard.append([

        InlineKeyboardButton(
            "📤 Upload File",
            callback_data="upload"
        )

    ])

    keyboard.append([

        InlineKeyboardButton(
            "🔙 Main Menu",
            callback_data="home"
        )

    ])

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# FILE CONTROLS
# =========================================================

def file_control_keyboard(
    filename
):

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(
                "▶️ Start",
                callback_data=
                f"start|{filename}"
            ),

            InlineKeyboardButton(
                "⏹️ Stop",
                callback_data=
                f"stop|{filename}"
            )

        ],

        [

            InlineKeyboardButton(
                "🔄 Restart",
                callback_data=
                f"restart|{filename}"
            )

        ],

        [

            InlineKeyboardButton(
                "📄 Logs",
                callback_data=
                f"logs|{filename}"
            ),

            InlineKeyboardButton(
                "🧹 Clear Logs",
                callback_data=
                f"clear_logs|{filename}"
            )

        ],

        [

            InlineKeyboardButton(
                "⌨️ Send Input",
                callback_data=
                f"input|{filename}"
            )

        ],

        [

            InlineKeyboardButton(
                "📦 Install Module",
                callback_data=
                f"install|{filename}"
            )

        ],

        [

            InlineKeyboardButton(
                "🗑️ Delete",
                callback_data=
                f"delete|{filename}"
            )

        ],

        [

            InlineKeyboardButton(
                "🔙 My Files",
                callback_data=
                "my_files"
            )

        ]

    ])


# =========================================================
# SHOW FILE
# =========================================================

async def show_file(
    query,
    filename
):

    status = (

        "🟢 Running"

        if is_running(filename)

        else

        "🔴 Stopped"

    )

    await query.edit_message_text(

        "╔════════════════════════════╗\n"
        "       📄 <b>FILE MANAGER</b>\n"
        "╚════════════════════════════╝\n\n"

        f"📄 <b>{filename}</b>\n\n"

        f"📊 Status: <b>{status}</b>\n\n"

        "Choose an action:",

        parse_mode="HTML",

        reply_markup=
        file_control_keyboard(
            filename
        )

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

    user = query.from_user

    if not user:
        return

    await query.answer()

    data = query.data or ""


    # =====================================================
    # ACCESS
    # =====================================================

    if not has_access(user.id):

        await query.answer(

            "🚫 Access denied.",

            show_alert=True

        )

        return


    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        await query.edit_message_text(

            "🏠 <b>MAIN MENU</b>\n\n"
            "Choose an option:",

            parse_mode="HTML",

            reply_markup=
            home_keyboard()

        )

        return


    # =====================================================
    # MY FILES
    # =====================================================

    if data == "my_files":

        files = get_user_files(
            user.id
        )

        if not files:

            await query.edit_message_text(

                "📁 <b>MY FILES</b>\n\n"
                "You don't have any uploaded files yet.",

                parse_mode="HTML",

                reply_markup=
                InlineKeyboardMarkup([

                    [

                        InlineKeyboardButton(
                            "📤 Upload File",
                            callback_data="upload"
                        )

                    ],

                    [

                        InlineKeyboardButton(
                            "🔙 Main Menu",
                            callback_data="home"
                        )

                    ]

                ])

            )

            return


        await query.edit_message_text(

            "📁 <b>MY FILES</b>\n\n"

            "🟢 Running\n"
            "🔴 Stopped\n\n"

            "Select a file:",

            parse_mode="HTML",

            reply_markup=
            files_keyboard(
                user.id
            )

        )

        return


    # =====================================================
    # STATISTICS
    # =====================================================

    if data == "stats":

        total = get_user_file_count(
            user.id
        )

        running = 0

        for filename in get_user_files(
            user.id
        ):

            if is_running(filename):

                running += 1

        stopped = total - running

        await query.edit_message_text(

            "📊 <b>MY STATISTICS</b>\n\n"

            f"📁 Total Files: <b>{total}</b>\n"
            f"🟢 Running: <b>{running}</b>\n"
            f"🔴 Stopped: <b>{stopped}</b>",

            parse_mode="HTML",

            reply_markup=
            InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "📁 My Files",
                        callback_data="my_files"
                    )

                ],

                [

                    InlineKeyboardButton(
                        "🔙 Main Menu",
                        callback_data="home"
                    )

                ]

            ])

        )

        return


    # =====================================================
    # HELP
    # =====================================================

    if data == "help":

        await query.edit_message_text(

            "ℹ️ <b>HELP</b>\n\n"

            "📤 Upload File — Upload a Python file.\n\n"

            "📁 My Files — Manage your files.\n\n"

            "▶️ Start — Start a file.\n\n"

            "⏹️ Stop — Stop a file.\n\n"

            "🔄 Restart — Restart a file.\n\n"

            "📄 Logs — View output logs.\n\n"

            "⌨️ Send Input — Send input to a running file.\n\n"

            "📦 Install Module — Install a required Python package.",

            parse_mode="HTML",

            reply_markup=
            InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "🔙 Main Menu",
                        callback_data="home"
                    )

                ]

            ])

        )

        return


    # =====================================================
    # UPLOAD
    # =====================================================

    if data == "upload":

        await query.message.reply_text(

            "📤 <b>UPLOAD FILE</b>\n\n"

            "Send your Python <code>.py</code> file here.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # FILE ACTIONS
    # =====================================================

    try:

        action, filename = data.split(
            "|",
            1
        )

    except ValueError:

        return


    # =====================================================
    # FILE OWNERSHIP
    # =====================================================

    if action == "file":

        if not user_owns_file(
            user.id,
            filename
        ):

            await query.answer(

                "🚫 You don't own this file.",

                show_alert=True

            )

            return

        await show_file(
            query,
            filename
        )

        return


    if not user_owns_file(
        user.id,
        filename
    ):

        await query.answer(

            "🚫 You don't own this file.",

            show_alert=True

        )

        return


    # =====================================================
    # START
    # =====================================================

    if action == "start":

        success, message = start_process(
            filename
        )

        await query.answer(
            message,
            show_alert=True
        )

        await show_file(
            query,
            filename
        )

        return


    # =====================================================
    # STOP
    # =====================================================

    if action == "stop":

        success, message = stop_process(
            filename
        )

        await query.answer(
            message,
            show_alert=True
        )

        await show_file(
            query,
            filename
        )

        return


    # =====================================================
    # RESTART
    # =====================================================

    if action == "restart":

        success, message = restart_process(
            filename
        )

        await query.answer(
            message,
            show_alert=True
        )

        await show_file(
            query,
            filename
        )

        return


    # =====================================================
    # LOGS
    # =====================================================

    if action == "logs":

        logs = get_logs(
            filename
        )

        if not logs:

            logs = "No logs available."

        if len(logs) > 3900:

            logs = logs[-3900:]

        await query.message.reply_text(

            f"📄 <b>LOGS</b>\n\n"
            f"📁 <code>{filename}</code>\n\n"
            f"<pre>{logs}</pre>",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # CLEAR LOGS
    # =====================================================

    if action == "clear_logs":

        result = clear_logs(
            filename
        )

        await query.answer(

            "✅ Logs cleared."
            if result
            else
            "❌ Failed to clear logs.",

            show_alert=True

        )

        return


    # =====================================================
    # INPUT
    # =====================================================

    if action == "input":

        context.user_data[
            "active_file"
        ] = filename

        await query.message.reply_text(

            f"⌨️ <b>INPUT MODE</b>\n\n"
            f"📄 <code>{filename}</code>\n\n"
            "Send the input value as a message.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # INSTALL MODULE
    # =====================================================

    if action == "install":

        context.user_data[
            "module_install_file"
        ] = filename

        await query.message.reply_text(

            "📦 <b>INSTALL MODULE</b>\n\n"

            "Send the Python package name.\n\n"

            "Example:\n"
            "<code>requests</code>",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # DELETE
    # =====================================================

    if action == "delete":

        await query.edit_message_text(

            "⚠️ <b>DELETE FILE?</b>\n\n"

            f"📄 <code>{filename}</code>\n\n"

            "This will stop the process and "
            "remove the uploaded file.\n\n"

            "Are you sure?",

            parse_mode="HTML",

            reply_markup=
            InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "⚠️ Yes, Delete",
                        callback_data=
                        f"confirm_delete|{filename}"
                    ),

                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data=
                        f"file|{filename}"
                    )

                ]

            ])

        )

        return


    # =====================================================
    # CONFIRM DELETE
    # =====================================================

    if action == "confirm_delete":

        if is_running(
            filename
        ):

            stop_process(
                filename
            )


        filepath = os.path.join(

            UPLOAD_FOLDER,

            filename

        )


        if os.path.exists(
            filepath
        ):

            try:

                os.remove(
                    filepath
                )

            except Exception as e:

                await query.answer(

                    f"❌ Delete failed: {e}",

                    show_alert=True

                )

                return


        remove_user_file(

            user.id,

            filename

        )


        await query.edit_message_text(

            "✅ <b>FILE DELETED</b>\n\n"

            f"📄 <code>{filename}</code>\n\n"

            "The file has been removed.",

            parse_mode="HTML",

            reply_markup=
            files_keyboard(
                user.id
            )

        )

        return
