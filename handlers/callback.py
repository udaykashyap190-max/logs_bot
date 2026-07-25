# =========================================================
# FILE: handlers/callback.py
# PART 9C-3
# =========================================================

from telegram import Update
from telegram.ext import ContextTypes

from core.auth import (
    has_access,
    is_admin
)

from core.process import (
    start_process,
    stop_process,
    restart_process,
    get_logs,
    clear_logs
)

# =========================================================
# ADMIN HANDLERS
# =========================================================

from handlers.admin import (
    admin_panel,
    show_pending,
    show_approved,
    show_blocked,
    show_stats,
    show_user,
    approve_user_callback,
    reject_user_callback,
    block_user_callback,
    delete_user_callback
)


# =========================================================
# MAIN CALLBACK HANDLER
# =========================================================

async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    # Answer callback first
    await query.answer()

    user = query.from_user

    user_id = user.id

    data = query.data or ""


    # =====================================================
    # ADMIN ROUTES
    # =====================================================

    # -----------------------------------------------------
    # ADMIN PANEL
    # -----------------------------------------------------

    if data == "admin_panel":

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await admin_panel(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # PENDING REQUESTS
    # -----------------------------------------------------

    if data == "admin_pending":

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await show_pending(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # APPROVED USERS
    # -----------------------------------------------------

    if data == "admin_approved":

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await show_approved(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # BLOCKED USERS
    # -----------------------------------------------------

    if data == "admin_blocked":

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await show_blocked(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # ADMIN STATISTICS
    # -----------------------------------------------------

    if data == "admin_stats":

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await show_stats(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # VIEW SPECIFIC USER
    # -----------------------------------------------------

    if data.startswith(
        "admin_user|"
    ):

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await show_user(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # APPROVE USER
    # -----------------------------------------------------

    if data.startswith(
        "approve|"
    ):

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await approve_user_callback(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # REJECT USER
    # -----------------------------------------------------

    if data.startswith(
        "reject|"
    ):

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await reject_user_callback(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # BLOCK USER
    # -----------------------------------------------------

    if data.startswith(
        "block|"
    ):

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await block_user_callback(
            update,
            context
        )

        return


    # -----------------------------------------------------
    # DELETE USER
    # -----------------------------------------------------

    if data.startswith(
        "delete_user|"
    ):

        if not is_admin(user_id):

            await query.answer(
                "🚫 Admin access required.",
                show_alert=True
            )

            return

        await delete_user_callback(
            update,
            context
        )

        return


    # =====================================================
    # NORMAL USER ACCESS CHECK
    # =====================================================

    # Admins automatically bypass normal user access.

    if not is_admin(user_id):

        if not has_access(user_id):

            await query.edit_message_text(

                "🚫 <b>ACCESS DENIED</b>\n\n"

                "Your account is not approved "
                "to use this bot yet.\n\n"

                "Please wait for the administrator "
                "to approve your request.",

                parse_mode="HTML"

            )

            return


    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        try:

            from handlers.start import (
                show_home
            )

            await show_home(
                update,
                context
            )

        except ImportError:

            await query.edit_message_text(

                "🏠 <b>HOME</b>\n\n"

                "Welcome back!",

                parse_mode="HTML"

            )

        return


    # =====================================================
    # START PROCESS
    # =====================================================

    if data.startswith(
        "start|"
    ):

        filename = data.split(
            "|",
            1
        )[1]


        try:

            result = start_process(
                filename
            )


            # If the process function
            # doesn't return anything

            if result is None:

                result = (
                    "Process started successfully."
                )


            await query.edit_message_text(

                "▶️ <b>PROCESS STARTED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"{result}",

                parse_mode="HTML"

            )


        except Exception as e:

            await query.edit_message_text(

                "❌ <b>START FAILED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"Error:\n"
                f"<code>{str(e)}</code>",

                parse_mode="HTML"

            )


        return


    # =====================================================
    # STOP PROCESS
    # =====================================================

    if data.startswith(
        "stop|"
    ):

        filename = data.split(
            "|",
            1
        )[1]


        try:

            result = stop_process(
                filename
            )


            if result is None:

                result = (
                    "Process stopped successfully."
                )


            await query.edit_message_text(

                "⏹️ <b>PROCESS STOPPED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"{result}",

                parse_mode="HTML"

            )


        except Exception as e:

            await query.edit_message_text(

                "❌ <b>STOP FAILED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"Error:\n"
                f"<code>{str(e)}</code>",

                parse_mode="HTML"

            )


        return


    # =====================================================
    # RESTART PROCESS
    # =====================================================

    if data.startswith(
        "restart|"
    ):

        filename = data.split(
            "|",
            1
        )[1]


        try:

            result = restart_process(
                filename
            )


            if result is None:

                result = (
                    "Process restarted successfully."
                )


            await query.edit_message_text(

                "🔄 <b>PROCESS RESTARTED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"{result}",

                parse_mode="HTML"

            )


        except Exception as e:

            await query.edit_message_text(

                "❌ <b>RESTART FAILED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"Error:\n"
                f"<code>{str(e)}</code>",

                parse_mode="HTML"

            )


        return


    # =====================================================
    # SHOW LOGS
    # =====================================================

    if data.startswith(
        "logs|"
    ):

        filename = data.split(
            "|",
            1
        )[1]


        try:

            logs = get_logs(
                filename
            )


            if not logs:

                logs = (
                    "📭 No logs available yet."
                )


            # Telegram message size protection

            if len(logs) > 3800:

                logs = (
                    logs[-3800:]
                )


            # Escape basic HTML characters

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


            await query.edit_message_text(

                "📄 <b>PROCESS LOGS</b>\n\n"

                f"📁 File: "
                f"<code>{filename}</code>\n\n"

                f"<pre>{logs}</pre>",

                parse_mode="HTML"

            )


        except Exception as e:

            await query.edit_message_text(

                "❌ <b>LOG ERROR</b>\n\n"

                f"<code>{str(e)}</code>",

                parse_mode="HTML"

            )


        return


    # =====================================================
    # CLEAR LOGS
    # =====================================================

    if data.startswith(
        "clear_logs|"
    ):

        filename = data.split(
            "|",
            1
        )[1]


        try:

            clear_logs(
                filename
            )


            await query.answer(

                "🧹 Logs cleared successfully.",

                show_alert=True

            )


        except Exception as e:

            await query.answer(

                f"❌ Error: {str(e)}",

                show_alert=True

            )


        return


    # =====================================================
    # UNKNOWN CALLBACK
    # =====================================================

    await query.answer(

        "⚠️ This button is not available.",

        show_alert=True

    )
