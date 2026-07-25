from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ContextTypes
)

from core.auth import has_access

from core.process import (
    start_process,
    stop_process,
    restart_process,
    is_running,
    get_logs,
    clear_logs
)


# =========================
# MAIN FILE CONTROL KEYBOARD
# =========================

def main_keyboard(
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

        ]

    ]


    return InlineKeyboardMarkup(
        keyboard
    )


# =========================
# CALLBACK HANDLER
# =========================

async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user


    if user is None:

        return


    # =========================
    # CHECK ACCESS
    # =========================

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


    # =========================
    # GET ACTION + FILENAME
    # =========================

    try:

        action, filename = query.data.split(

            "|",

            1

        )

    except ValueError:

        return


    # =========================
    # START
    # =========================

    if action == "start":

        success, message = start_process(

            filename

        )


        context.user_data[

            "active_file"

        ] = filename


    # =========================
    # STOP
    # =========================

    elif action == "stop":

        success, message = stop_process(

            filename

        )


    # =========================
    # RESTART
    # =========================

    elif action == "restart":

        success, message = restart_process(

            filename

        )


        context.user_data[

            "active_file"

        ] = filename


    # =========================
    # LOGS
    # =========================

    elif action == "logs":

        logs = get_logs(

            filename

        )


        if len(logs) > 3900:

            logs = logs[-3900:]


        await query.message.reply_text(

            f"📄 Logs\n\n"

            f"📁 File: `{filename}`\n\n"

            f"```text\n"
            f"{logs}\n"
            f"```",

            parse_mode="Markdown"

        )


        return


    # =========================
    # CLEAR LOGS
    # =========================

    elif action == "clear_logs":

        success = clear_logs(

            filename

        )


        if success:

            await query.answer(

                "🧹 Logs cleared.",

                show_alert=True

            )

        else:

            await query.answer(

                "❌ Failed to clear logs.",

                show_alert=True

            )


        return


    # =========================
    # SEND INPUT
    # =========================

    elif action == "input":

        if not is_running(

            filename

        ):

            await query.answer(

                "❌ This file is not running.",

                show_alert=True

            )

            return


        context.user_data[

            "active_file"

        ] = filename


        await query.message.reply_text(

            f"⌨️ Input Mode Enabled\n\n"

            f"📄 File: `{filename}`\n\n"

            f"Send your input as a normal "
            f"Telegram message.\n\n"

            f"Your message will be sent "
            f"to the running file.",

            parse_mode="Markdown"

        )


        return


    # =========================
    # UNKNOWN ACTION
    # =========================

    else:

        return


    # =========================
    # UPDATE STATUS
    # =========================

    if is_running(

        filename

    ):

        status = "🟢 Running"

    else:

        status = "🔴 Stopped"


    await query.edit_message_text(

        text=(

            f"📄 File: `{filename}`\n\n"

            f"📊 Status: {status}\n\n"

            f"{message}"

        ),

        parse_mode="Markdown",

        reply_markup=main_keyboard(

            filename

        )

    )