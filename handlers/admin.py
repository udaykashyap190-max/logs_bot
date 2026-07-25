from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes

from core.auth import is_admin

from database import (
    get_pending_users,
    get_approved_users,
    get_blocked_users,
    set_user_status,
    delete_user,
    get_total_users,
    get_pending_count,
    get_approved_count,
    get_blocked_count,
    get_total_files
)


# =========================================================
# ADMIN MAIN MENU
# =========================================================

def admin_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "📋 Pending Requests",
                callback_data="admin_pending"
            )
        ],

        [
            InlineKeyboardButton(
                "✅ Approved Users",
                callback_data="admin_approved"
            ),

            InlineKeyboardButton(
                "🚫 Blocked Users",
                callback_data="admin_blocked"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="admin_stats"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 Main Menu",
                callback_data="home"
            )
        ]

    ])


# =========================================================
# ADMIN PANEL
# =========================================================

async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user_id = query.from_user.id

    if not is_admin(user_id):

        await query.answer(
            "🚫 Admin access required.",
            show_alert=True
        )

        return

    await query.answer()

    await query.edit_message_text(

        "╔══════════════════════════╗\n"
        "      👑 <b>ADMIN PANEL</b>\n"
        "╚══════════════════════════╝\n\n"

        "Manage users and monitor your bot.\n\n"

        "Choose an option below:",

        parse_mode="HTML",

        reply_markup=admin_keyboard()

    )


# =========================================================
# PENDING USERS
# =========================================================

async def show_pending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "🚫 Admin access required.",
            show_alert=True
        )

        return

    await query.answer()

    users = get_pending_users()

    if not users:

        await query.edit_message_text(

            "📋 <b>PENDING REQUESTS</b>\n\n"

            "✅ There are no pending requests.",

            parse_mode="HTML",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin_panel"
                    )
                ]

            ])

        )

        return


    text = (
        "📋 <b>PENDING REQUESTS</b>\n\n"
        "Select a user to manage:\n\n"
    )

    keyboard = []


    for user in users:

        user_id = user["user_id"]

        username = user["username"]

        first_name = (
            user["first_name"]
            or "Unknown"
        )

        text += (

            f"👤 <b>{first_name}</b>\n"

            f"🔹 @{username or 'N/A'}\n"

            f"🆔 <code>{user_id}</code>\n\n"

        )


        keyboard.append([

            InlineKeyboardButton(

                f"👤 {first_name}",

                callback_data=
                f"admin_user|{user_id}"

            )

        ])


    keyboard.append([

        InlineKeyboardButton(

            "🔄 Refresh",

            callback_data=
            "admin_pending"

        )

    ])


    keyboard.append([

        InlineKeyboardButton(

            "🔙 Admin Panel",

            callback_data=
            "admin_panel"

        )

    ])


    await query.edit_message_text(

        text,

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )

    )


# =========================================================
# USER MANAGEMENT SCREEN
# =========================================================

async def show_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "🚫 Admin access required.",
            show_alert=True
        )

        return

    await query.answer()


    try:

        _, user_id = query.data.split(
            "|",
            1
        )

        user_id = int(user_id)

    except (
        ValueError,
        TypeError
    ):

        await query.answer(
            "❌ Invalid user.",
            show_alert=True
        )

        return


    from database import get_user

    user = get_user(
        user_id
    )


    if not user:

        await query.edit_message_text(

            "❌ User not found.",

            reply_markup=
            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data=
                        "admin_panel"
                    )
                ]

            ])

        )

        return


    first_name = (
        user["first_name"]
        or "Unknown"
    )

    username = (
        user["username"]
        or "N/A"
    )

    status = user["status"]


    text = (

        "👤 <b>USER DETAILS</b>\n\n"

        f"👤 Name: <b>{first_name}</b>\n"

        f"🔹 Username: @{username}\n"

        f"🆔 ID: <code>{user_id}</code>\n"

        f"📊 Status: <b>{status.upper()}</b>\n"

        f"📅 Joined: <code>{user['joined_at']}</code>\n\n"

        "Choose an action:"

    )


    keyboard = []


    if status == "pending":

        keyboard.append([

            InlineKeyboardButton(

                "✅ Approve",

                callback_data=
                f"approve|{user_id}"

            ),

            InlineKeyboardButton(

                "🚫 Reject",

                callback_data=
                f"reject|{user_id}"

            )

        ])


    elif status == "approved":

        keyboard.append([

            InlineKeyboardButton(

                "🚫 Remove Access",

                callback_data=
                f"block|{user_id}"

            )

        ])


    elif status in (
        "blocked",
        "rejected"
    ):

        keyboard.append([

            InlineKeyboardButton(

                "♻️ Approve Again",

                callback_data=
                f"approve|{user_id}"

            )

        ])


    keyboard.append([

        InlineKeyboardButton(

            "🗑️ Delete User",

            callback_data=
            f"delete_user|{user_id}"

        )

    ])


    keyboard.append([

        InlineKeyboardButton(

            "🔙 Back",

            callback_data=
            "admin_pending"

        )

    ])


    await query.edit_message_text(

        text,

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )

    )


# =========================================================
# APPROVED USERS
# =========================================================

async def show_approved(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "🚫 Admin access required.",
            show_alert=True
        )

        return

    await query.answer()

    users = get_approved_users()

    text = (
        "✅ <b>APPROVED USERS</b>\n\n"
    )

    keyboard = []


    if not users:

        text += (
            "No approved users."
        )


    else:

        for user in users:

            user_id = user["user_id"]

            first_name = (
                user["first_name"]
                or "Unknown"
            )

            username = (
                user["username"]
                or "N/A"
            )


            text += (

                f"👤 <b>{first_name}</b>\n"

                f"🔹 @{username}\n"

                f"🆔 <code>{user_id}</code>\n\n"

            )


            keyboard.append([

                InlineKeyboardButton(

                    f"👤 {first_name}",

                    callback_data=
                    f"admin_user|{user_id}"

                )

            ])


    keyboard.append([

        InlineKeyboardButton(

            "🔄 Refresh",

            callback_data=
            "admin_approved"

        )

    ])


    keyboard.append([

        InlineKeyboardButton(

            "🔙 Admin Panel",

            callback_data=
            "admin_panel"

        )

    ])


    await query.edit_message_text(

        text,

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )

    )


# =========================================================
# BLOCKED USERS
# =========================================================

async def show_blocked(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "🚫 Admin access required.",
            show_alert=True
        )

        return

    await query.answer()

    users = get_blocked_users()

    text = (
        "🚫 <b>BLOCKED USERS</b>\n\n"
    )

    keyboard = []


    if not users:

        text += (
            "No blocked users."
        )


    else:

        for user in users:

            user_id = user["user_id"]

            first_name = (
                user["first_name"]
                or "Unknown"
            )


            text += (

                f"👤 <b>{first_name}</b>\n"

                f"🆔 <code>{user_id}</code>\n"

                f"📊 Status: "
                f"<b>{user['status']}</b>\n\n"

            )


            keyboard.append([

                InlineKeyboardButton(

                    f"👤 {first_name}",

                    callback_data=
                    f"admin_user|{user_id}"

                )

            ])


    keyboard.append([

        InlineKeyboardButton(

            "🔄 Refresh",

            callback_data=
            "admin_blocked"

        )

    ])


    keyboard.append([

        InlineKeyboardButton(

            "🔙 Admin Panel",

            callback_data=
            "admin_panel"

        )

    ])


    await query.edit_message_text(

        text,

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )

    )


# =========================================================
# STATISTICS
# =========================================================

async def show_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not is_admin(
        query.from_user.id
    ):

        await query.answer(
            "🚫 Admin access required.",
            show_alert=True
        )

        return

    await query.answer()


    total_users = (
        get_total_users()
    )

    pending = (
        get_pending_count()
    )

    approved = (
        get_approved_count()
    )

    blocked = (
        get_blocked_count()
    )

    total_files = (
        get_total_files()
    )


    await query.edit_message_text(

        "╔══════════════════════════╗\n"
        "       📊 <b>BOT STATISTICS</b>\n"
        "╚══════════════════════════╝\n\n"

        f"👥 Total Users: "
        f"<b>{total_users}</b>\n\n"

        f"📋 Pending: "
        f"<b>{pending}</b>\n\n"

        f"✅ Approved: "
        f"<b>{approved}</b>\n\n"

        f"🚫 Blocked: "
        f"<b>{blocked}</b>\n\n"

        f"📁 Total Files: "
        f"<b>{total_files}</b>",

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "🔄 Refresh",

                    callback_data=
                    "admin_stats"

                )

            ],

            [

                InlineKeyboardButton(

                    "🔙 Admin Panel",

                    callback_data=
                    "admin_panel"

                )

            ]

        ])

    )


# =========================================================
# APPROVE USER
# =========================================================

async def approve_user_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    admin_id = (
        query.from_user.id
    )


    if not is_admin(
        admin_id
    ):

        await query.answer(

            "🚫 Admin access required.",

            show_alert=True

        )

        return


    try:

        _, user_id = query.data.split(
            "|",
            1
        )

        user_id = int(
            user_id
        )

    except (
        ValueError,
        TypeError
    ):

        await query.answer(

            "❌ Invalid user ID.",

            show_alert=True

        )

        return


    set_user_status(

        user_id,

        "approved"

    )


    await query.answer(

        "✅ User approved."

    )


    # Notify user

    try:

        await context.bot.send_message(

            chat_id=user_id,

            text=(

                "🎉 <b>ACCESS APPROVED!</b>\n\n"

                "Your request to use the "
                "bot has been approved.\n\n"

                "You can now send /start "
                "and use the bot.",

            ),

            parse_mode="HTML"

        )

    except Exception:

        pass


    await query.edit_message_text(

        "✅ <b>USER APPROVED</b>\n\n"

        f"🆔 User ID: "
        f"<code>{user_id}</code>\n\n"

        "🔔 The user has been notified.",

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "📋 Pending Requests",

                    callback_data=
                    "admin_pending"

                )

            ],

            [

                InlineKeyboardButton(

                    "🔙 Admin Panel",

                    callback_data=
                    "admin_panel"

                )

            ]

        ])

    )


# =========================================================
# REJECT USER
# =========================================================

async def reject_user_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "🚫 Admin access required.",

            show_alert=True

        )

        return


    try:

        _, user_id = query.data.split(
            "|",
            1
        )

        user_id = int(
            user_id
        )

    except (
        ValueError,
        TypeError
    ):

        await query.answer(

            "❌ Invalid user ID.",

            show_alert=True

        )

        return


    set_user_status(

        user_id,

        "rejected"

    )


    await query.answer(

        "🚫 User rejected."

    )


    try:

        await context.bot.send_message(

            chat_id=user_id,

            text=(

                "🚫 <b>ACCESS REQUEST REJECTED</b>\n\n"

                "Your request to use the "
                "bot was rejected by the administrator."

            ),

            parse_mode="HTML"

        )

    except Exception:

        pass


    await query.edit_message_text(

        "🚫 <b>USER REJECTED</b>\n\n"

        f"🆔 User ID: "
        f"<code>{user_id}</code>\n\n"

        "🔔 The user has been notified.",

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "📋 Pending Requests",

                    callback_data=
                    "admin_pending"

                )

            ],

            [

                InlineKeyboardButton(

                    "🔙 Admin Panel",

                    callback_data=
                    "admin_panel"

                )

            ]

        ])

    )


# =========================================================
# BLOCK USER
# =========================================================

async def block_user_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "🚫 Admin access required.",

            show_alert=True

        )

        return


    try:

        _, user_id = query.data.split(
            "|",
            1
        )

        user_id = int(
            user_id
        )

    except (
        ValueError,
        TypeError
    ):

        await query.answer(

            "❌ Invalid user ID.",

            show_alert=True

        )

        return


    set_user_status(

        user_id,

        "blocked"

    )


    await query.answer(

        "🚫 User blocked."

    )


    try:

        await context.bot.send_message(

            chat_id=user_id,

            text=(

                "🚫 <b>ACCESS REMOVED</b>\n\n"

                "Your access to the bot "
                "has been removed by the administrator."

            ),

            parse_mode="HTML"

        )

    except Exception:

        pass


    await query.edit_message_text(

        "🚫 <b>USER BLOCKED</b>\n\n"

        f"🆔 User ID: "
        f"<code>{user_id}</code>",

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "👥 Approved Users",

                    callback_data=
                    "admin_approved"

                )

            ],

            [

                InlineKeyboardButton(

                    "🔙 Admin Panel",

                    callback_data=
                    "admin_panel"

                )

            ]

        ])

    )


# =========================================================
# DELETE USER
# =========================================================

async def delete_user_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    if not is_admin(
        query.from_user.id
    ):

        await query.answer(

            "🚫 Admin access required.",

            show_alert=True

        )

        return


    try:

        _, user_id = query.data.split(
            "|",
            1
        )

        user_id = int(
            user_id
        )

    except (
        ValueError,
        TypeError
    ):

        await query.answer(

            "❌ Invalid user ID.",

            show_alert=True

        )

        return


    delete_user(

        user_id

    )


    await query.answer(

        "🗑️ User deleted."

    )


    await query.edit_message_text(

        "🗑️ <b>USER DELETED</b>\n\n"

        f"🆔 User ID: "
        f"<code>{user_id}</code>\n\n"

        "The user's database record "
        "and file ownership records "
        "have been removed.",

        parse_mode="HTML",

        reply_markup=
        InlineKeyboardMarkup([

            [

                InlineKeyboardButton(

                    "🚫 Blocked Users",

                    callback_data=
                    "admin_blocked"

                )

            ],

            [

                InlineKeyboardButton(

                    "🔙 Admin Panel",

                    callback_data=
                    "admin_panel"

                )

            ]

        ])

    )
