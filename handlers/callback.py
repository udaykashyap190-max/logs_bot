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
    get_user_file_count,
    get_total_users,
    get_approved_users,
    get_pending_users,
    get_total_files
)


UPLOAD_FOLDER = "uploads"


# =========================================================
# MAIN MENU
# =========================================================

def home_keyboard():

    keyboard = [

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
                "📊 My Statistics",
                callback_data="stats"
            ),

            InlineKeyboardButton(
                "ℹ️ Help",
                callback_data="help"
            )
        ]

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# FILE LIST
# =========================================================

def files_keyboard(
    user_id
):

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
                "🔙 Main Menu",
                callback_data="home"
            )

        ]

    )

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# FILE CONTROL KEYBOARD
# =========================================================

def file_control_keyboard(
    filename
):

    keyboard = [

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
                "🗑️ Delete File",
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

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# FILE SCREEN
# =========================================================

async def show_file(
    query,
    filename
):

    if is_running(filename):

        status = "🟢 Running"

    else:

        status = "🔴 Stopped"

    text = (

        "╔════════════════════════════╗\n"
        "        📄 <b>FILE MANAGER</b>\n"
        "╚════════════════════════════╝\n\n"

        f"📄 <b>{filename}</b>\n\n"

        f"📊 Status: <b>{status}</b>\n\n"

        "Choose an action:"
    )

    await query.edit_message_text(

        text,

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

    data = query.data or ""

    # =====================================================
    # ACCESS CHECK
    # =====================================================

    if not has_access(
        user.id
    ):

        await query.answer(

            "🚫 You don't have permission "
            "to use this bot.",

            show_alert=True

        )

        return

    await query.answer()


    # =====================================================
    # SIMPLE ACTIONS
    # =====================================================

    if data == "home":

        await query.edit_message_text(

            "🏠 <b>MAIN MENU</b>\n\n"
            "Choose an option below:",

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

            keyboard = [

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

            ]

            await query.edit_message_text(

                "📁 <b>MY FILES</b>\n\n"

                "You haven't uploaded "
                "any files yet.",

                parse_mode="HTML",

                reply_markup=
                InlineKeyboardMarkup(
                    keyboard
                )

            )

            return


        await query.edit_message_text(

            "╔════════════════════════════╗\n"
            "          📁 <b>MY FILES</b>\n"
            "╚════════════════════════════╝\n\n"

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

        total_files = get_user_file_count(
            user.id
        )

        running = 0

        for filename in get_user_files(
            user.id
        ):

            if is_running(filename):

                running += 1


        stopped = (
            total_files - running
        )


        text = (

            "📊 <b>MY STATISTICS</b>\n\n"

            f"📁 Total Files: <b>{total_files}</b>\n"

            f"🟢 Running: <b>{running}</b>\n"

            f"🔴 Stopped: <b>{stopped}</b>\n"

        )


        keyboard = [

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

        ]


        await query.edit_message_text(

            text,

            parse_mode="HTML",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )

        return


    # =====================================================
    # HELP
    # =====================================================

    if data == "help":

        text = (

            "ℹ️ <b>HELP</b>\n\n"

            "📤 <b>Upload File</b>\n"
            "Upload a Python file to the bot.\n\n"

            "📁 <b>My Files</b>\n"
            "View and manage all your uploaded files.\n\n"

            "▶️ <b>Start</b>\n"
            "Start a file.\n\n"

            "⏹️ <b>Stop</b>\n"
            "Stop a running file.\n\n"

            "🔄 <b>Restart</b>\n"
            "Restart a file.\n\n"

            "📄 <b>Logs</b>\n"
            "View the file output.\n\n"

            "⌨️ <b>Send Input</b>\n"
            "Send input to a running file.\n\n"

            "📦 <b>Install Module</b>\n"
            "Install a Python package."
        )


        keyboard = [

            [

                InlineKeyboardButton(
                    "🔙 Main Menu",
                    callback_data="home"
                )

            ]

        ]


        await query.edit_message_text(

            text,

            parse_mode="HTML",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )

        return


    # =====================================================
    # FILE-SPECIFIC ACTION
    # =====================================================

    try:

        action, filename = data.split(
            "|",
            1
        )

    except ValueError:

        return


    # =====================================================
    # OWNERSHIP CHECK
    # =====================================================

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

        context.user_data[
            "active_file"
        ] = filename


    # =====================================================
    # STOP
    # =====================================================

    elif action == "stop":

        success, message = stop_process(
            filename
        )


    # =====================================================
    # RESTART
    # =====================================================

    elif action == "restart":

        success, message = restart_process(
            filename
        )

        context.user_data[
            "active_file"
        ] = filename


    # =====================================================
    # LOGS
    # =====================================================

    elif action == "logs":

        logs = get_logs(
            filename
        )


        if len(logs) > 3900:

            logs = logs[
                -3900:
            ]


        await query.message.reply_text(

            f"📄 <b>LOGS</b>\n\n"
            f"📁 <b>{filename}</b>\n\n"
            f"<pre>{logs}</pre>",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # CLEAR LOGS
    # =====================================================

    elif action == "clear_logs":

        success = clear_logs(
            filename
        )


        await query.answer(

            "🧹 Logs cleared."
            if success
            else
            "❌ Failed to clear logs.",

            show_alert=True

        )

        return


    # =====================================================
    # SEND INPUT
    # =====================================================

    elif action == "input":

        if not is_running(
            filename
        ):

            await query.answer(

                "❌ File is not running.",

                show_alert=True

            )

            return


        context.user_data[
            "active_file"
        ] = filename


        await query.message.reply_text(

            f"⌨️ <b>INPUT MODE</b>\n\n"

            f"📄 File: <code>{filename}</code>\n\n"

            "Send your input as a normal "
            "Telegram message.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # INSTALL MODULE
    # =====================================================

    elif action == "install":

        context.user_data[
            "module_install_file"
        ] = filename


        await query.message.reply_text(

            "📦 <b>INSTALL PYTHON MODULE</b>\n\n"

            "Send the Python package name.\n\n"

            "Example:\n"
            "<code>requests</code>\n\n"

            "Only send the package name.",

            parse_mode="HTML"

        )

        return


    # =====================================================
    # DELETE CONFIRMATION
    # =====================================================

    elif action == "delete":

        keyboard = [

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

        ]


        await query.edit_message_text(

            "⚠️ <b>DELETE FILE?</b>\n\n"

            f"📄 <code>{filename}</code>\n\n"

            "This will remove the file from "
            "your uploaded files.\n\n"

            "Are you sure?",

            parse_mode="HTML",

            reply_markup=
            InlineKeyboardMarkup(
                keyboard
            )

        )

        return


    # =====================================================
    # CONFIRM DELETE
    # =====================================================

    elif action == "confirm_delete":

        filepath = os.path.join(

            UPLOAD_FOLDER,

            filename

        )


        # Stop process first
        if is_running(
            filename
        ):

            stop_process(
                filename
            )


        # Delete physical file
        deleted_from_disk = False


        if os.path.exists(
            filepath
        ):

            try:

                os.remove(
                    filepath
                )

                deleted_from_disk = True

            except Exception:

                deleted_from_disk = False


        # Remove database ownership
        removed_from_db = remove_user_file(

            user.id,

            filename

        )


        if removed_from_db:

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

        else:

            await query.answer(

                "❌ File could not be deleted.",

                show_alert=True

            )

        return


    else:

        return


    # =====================================================
    # REFRESH FILE SCREEN
    # =====================================================

    await show_file(

        query,

        filename

    )
