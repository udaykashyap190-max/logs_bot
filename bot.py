# =========================================================
# FILE: bot.py
# PART 9E
# =========================================================

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from handlers.start import start

from handlers.upload import upload_file

from handlers.callback import (
    handle_callback
)

from handlers.input import (
    handle_input
)


# =========================================================
# BUILD APPLICATION
# =========================================================

app = (
    Application.builder()

    .token(BOT_TOKEN)

    .build()
)


# =========================================================
# COMMAND HANDLERS
# =========================================================

app.add_handler(

    CommandHandler(
        "start",
        start
    )

)


# =========================================================
# FILE UPLOAD HANDLER
# =========================================================

app.add_handler(

    MessageHandler(

        filters.Document.ALL,

        upload_file

    )

)


# =========================================================
# CALLBACK HANDLER
# =========================================================

app.add_handler(

    CallbackQueryHandler(

        handle_callback

    )

)


# =========================================================
# TEXT INPUT HANDLER
# =========================================================

app.add_handler(

    MessageHandler(

        filters.TEXT
        & ~filters.COMMAND,

        handle_input

    )

)


# =========================================================
# START BOT
# =========================================================

print(
    "✅ Bot Started Successfully"
)


app.run_polling()
