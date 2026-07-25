# =========================================================
# SEND INPUT MODE
# =========================================================

if data.startswith(
    "input|"
):

    filename = data.split(
        "|",
        1
    )[1]


    # Check if process is running

    if not is_running(
        filename
    ):

        await query.answer(

            "❌ This file is not running.",

            show_alert=True

        )

        return


    # Save selected file

    context.user_data[
        "active_file"
    ] = filename


    await query.message.reply_text(

        "⌨️ <b>INPUT MODE ENABLED</b>\n\n"

        f"📄 File: "
        f"<code>{filename}</code>\n\n"

        "This file is now selected for input.\n\n"

        "Whenever the running file asks for:\n"
        "• API Key\n"
        "• Chat ID\n"
        "• Username\n"
        "• Password\n"
        "• Any other value\n\n"

        "👉 Simply send your answer as a normal "
        "Telegram message.\n\n"

        "Your message will be sent to this file.",

        parse_mode="HTML"

    )

    return
