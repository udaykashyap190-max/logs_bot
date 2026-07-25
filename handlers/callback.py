from telegram import Update
from telegram.ext import ContextTypes

from core.auth import (
    is_admin,
    has_access
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
# EXISTING USER HANDLERS
# =========================================================

# IMPORTANT:
# These imports must match the actual function names
# in your existing project.

from core.process import (
    start_process,
    stop_process,
    restart_process,
    get_logs,
    clear_logs,
    send_input
)


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def handle_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:

        return


    await query.answer()


    user_id = (
        query.from_user.id
    )

    data = (
        query.data
        or ""
    )


    # =====================================================
    # ADMIN ROUTES
    # =====================================================

    # Admin Panel

    if data == "admin_panel":

        if not is_admin(
            user_id
        ):

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


    # Pending Requests

    if data == "admin_pending":

        if not is_admin(
            user_id
        ):

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


    # Approved Users

    if data == "admin_approved":

        if not is_admin(
            user_id
        ):

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


    # Blocked Users

    if data == "admin_blocked":

        if not is_admin(
            user_id
        ):

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


    # Statistics

    if data == "admin_stats":

        if not is_admin(
            user_id
        ):

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


    # User Management

    if data.startswith(
        "admin_user|"
    ):

        if not is_admin(
            user_id
        ):

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


    # Approve User

    if data.startswith(
        "approve|"
    ):

        if not is_admin(
            user_id
        ):

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


    # Reject User

    if data.startswith(
        "reject|"
    ):

        if not is_admin(
            user_id
        ):

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


    # Block User

    if data.startswith(
        "block|"
    ):

        if not is_admin(
            user_id
        ):

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


    # Delete User

    if data.startswith(
        "delete_user|"
    ):

        if not is_admin(
            user_id
        ):

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
    # USER ACCESS CHECK
    # =====================================================

    # Admins bypass normal user access checks.

    if not is_admin(
        user_id
    ):

        if not has_access(
            user_id
        ):

            await query.edit_message_text(

                "🚫 <b>ACCESS DENIED</b>\n\n"

                "Your account is not approved "
                "to use this bot yet.",

                parse_mode="HTML"

            )

            return


    # =====================================================
    # HOME
    # =====================================================

    if data == "home":

        from handlers.start import (
            show_home
        )

        await show_home(
            update,
            context
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

            result = await start_process(

                user_id,

                filename

            )


            await query.edit_message_text(

                f"▶️ <b>PROCESS STARTED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"{result}",

                parse_mode="HTML"

            )

        except Exception as e:

            await query.edit_message_text(

                "❌ <b>START FAILED</b>\n\n"

                f"<code>{e}</code>",

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

            result = await stop_process(

                user_id,

                filename

            )


            await query.edit_message_text(

                f"⏹️ <b>PROCESS STOPPED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"{result}",

                parse_mode="HTML"

            )

        except Exception as e:

            await query.edit_message_text(

                "❌ <b>STOP FAILED</b>\n\n"

                f"<code>{e}</code>",

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

            result = await restart_process(

                user_id,

                filename

            )


            await query.edit_message_text(

                f"🔄 <b>PROCESS RESTARTED</b>\n\n"

                f"📄 File: "
                f"<code>{filename}</code>\n\n"

                f"{result}",

                parse_mode="HTML"

            )

        except Exception as e:

            await query.edit_message_text(

                "❌ <b>RESTART FAILED</b>\n\n"

                f"<code>{e}</code>",

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

                user_id,

                filename

            )


            if not logs:

                logs = (
                    "📭 No logs available yet."
                )


            # Telegram message limit protection

            if len(logs) > 3800:

                logs = logs[
                    -3800:
                ]


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

                f"<code>{e}</code>",

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

                user_id,

                filename

            )


            await query.answer(

                "🧹 Logs cleared.",

                show_alert=True

            )

        except Exception as e:

            await query.answer(

                f"❌ Error: {e}",

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
