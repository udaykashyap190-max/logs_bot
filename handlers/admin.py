from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ContextTypes
)

from core.auth import (
    is_admin
)

from database import (
    get_pending_users,
    get_approved_users,
    get_blocked_users,
    set_user_status
)


def admin_keyboard():

    keyboard = [

        [

            InlineKeyboardButton(
                "📋 Pending Users",
                callback_data="admin_pending"
            )

        ],

        [

            InlineKeyboardButton(
                "✅ Approved Users",
                callback_data="admin_approved"
            )

        ],

        [

            InlineKeyboardButton(
                "🚫 Blocked Users",
                callback_data="admin_blocked"
            )

        ]

    ]


    return InlineKeyboardMarkup(
        keyboard
    )


async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user


    if not is_admin(
        user.id
    ):

        await query.answer(

            "❌ Admin access only.",

            show_alert=True

        )

        return


    await query.answer()


    await query.edit_message_text(

        "👑 Admin Panel\n\n"

        "Manage users who can access "
        "the file runner.",

        reply_markup=
        admin_keyboard()

    )


async def show_pending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user


    if not is_admin(
        user.id
    ):

        await query.answer(

            "❌ Admin access only.",

            show_alert=True

        )

        return


    await query.answer()


    users = get_pending_users()


    if not users:

        await query.edit_message_text(

            "📋 Pending Users\n\n"

            "✅ No pending access requests.",

            reply_markup=
            admin_keyboard()

        )

        return


    text = (
        "📋 Pending Users\n\n"
    )


    keyboard = []


    for (

        user_id,

        username,

        first_name,

        joined_at

    ) in users:


        display_name = (
            first_name
            or
            "Unknown"
        )


        username_text = (

            f"@{username}"

            if username

            else

            "No username"

        )


        text += (

            f"👤 {display_name}\n"

            f"🔹 {username_text}\n"

            f"🆔 `{user_id}`\n\n"

        )


        keyboard.append(

            [

                InlineKeyboardButton(

                    f"✅ Approve {display_name}",

                    callback_data=
                    f"approve|{user_id}"

                )

            ]

        )


        keyboard.append(

            [

                InlineKeyboardButton(

                    f"❌ Reject {display_name}",

                    callback_data=
                    f"reject|{user_id}"

                )

            ]

        )


    keyboard.append(

        [

            InlineKeyboardButton(

                "🔙 Back",

                callback_data=
                "admin_panel"

            )

        ]

    )


    await query.edit_message_text(

        text,

        parse_mode="Markdown",

        reply_markup=
        InlineKeyboardMarkup(
            keyboard
        )

    )


async def show_approved(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user


    if not is_admin(
        user.id
    ):

        await query.answer(

            "❌ Admin access only.",

            show_alert=True

        )

        return


    await query.answer()


    users = get_approved_users()


    if not users:

        text = (

            "✅ Approved Users\n\n"

            "No approved users."

        )


    else:

        text = (

            "✅ Approved Users\n\n"

        )


        for (

            user_id,

            username,

            first_name,

            joined_at

        ) in users:


            text += (

                f"👤 {first_name or 'Unknown'}\n"

                f"🔹 @{username if username else 'N/A'}\n"

                f"🆔 `{user_id}`\n\n"

            )


    await query.edit_message_text(

        text,

        parse_mode="Markdown",

        reply_markup=
        InlineKeyboardMarkup(

            [

                [

                    InlineKeyboardButton(

                        "🔙 Back",

                        callback_data=
                        "admin_panel"

                    )

                ]

            ]

        )

    )


async def show_blocked(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user


    if not is_admin(
        user.id
    ):

        await query.answer(

            "❌ Admin access only.",

            show_alert=True

        )

        return


    await query.answer()


    users = get_blocked_users()


    if not users:

        text = (

            "🚫 Blocked Users\n\n"

            "No blocked users."

        )


    else:

        text = (

            "🚫 Blocked Users\n\n"

        )


        for (

            user_id,

            username,

            first_name,

            joined_at

        ) in users:


            text += (

                f"👤 {first_name or 'Unknown'}\n"

                f"🔹 @{username if username else 'N/A'}\n"

                f"🆔 `{user_id}`\n\n"

            )


    await query.edit_message_text(

        text,

        parse_mode="Markdown",

        reply_markup=
        InlineKeyboardMarkup(

            [

                [

                    InlineKeyboardButton(

                        "🔙 Back",

                        callback_data=
                        "admin_panel"

                    )

                ]

            ]

        )

    )


async def approve_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user


    if not is_admin(
        user.id
    ):

        await query.answer(

            "❌ Admin access only.",

            show_alert=True

        )

        return


    await query.answer()


    _, user_id = query.data.split(
        "|",
        1
    )


    set_user_status(

        int(user_id),

        "approved"

    )


    await query.edit_message_text(

        f"✅ User `{user_id}` approved.",

        parse_mode="Markdown",

        reply_markup=
        InlineKeyboardMarkup(

            [

                [

                    InlineKeyboardButton(

                        "📋 Pending Users",

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

            ]

        )

    )


async def reject_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user


    if not is_admin(
        user.id
    ):

        await query.answer(

            "❌ Admin access only.",

            show_alert=True

        )

        return


    await query.answer()


    _, user_id = query.data.split(
        "|",
        1
    )


    set_user_status(

        int(user_id),

        "blocked"

    )


    await query.edit_message_text(

        f"🚫 User `{user_id}` rejected.",

        parse_mode="Markdown",

        reply_markup=
        InlineKeyboardMarkup(

            [

                [

                    InlineKeyboardButton(

                        "📋 Pending Users",

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

            ]

        )

    )