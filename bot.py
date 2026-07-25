import asyncio

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN

from database import init_database

from handlers.start import start
from handlers.upload import upload_file
from handlers.callback import handle_callback
from handlers.input import handle_input

from handlers.admin import (
    admin_panel,
    show_pending,
    show_approved,
    show_blocked,
    approve_user,
    reject_user,
)


# =========================
# INITIALIZE DATABASE
# =========================

init_database()


# =========================
# CREATE BOT APPLICATION
# =========================

app = (
    Application
    .builder()
    .token(BOT_TOKEN)
    .build()
)


# =========================
# START COMMAND
# =========================

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)


# =========================
# ADMIN PANEL CALLBACKS
# =========================

app.add_handler(
    CallbackQueryHandler(
        admin_panel,
        pattern=r"^admin_panel$"
    )
)


app.add_handler(
    CallbackQueryHandler(
        show_pending,
        pattern=r"^admin_pending$"
    )
)


app.add_handler(
    CallbackQueryHandler(
        show_approved,
        pattern=r"^admin_approved$"
    )
)


app.add_handler(
    CallbackQueryHandler(
        show_blocked,
        pattern=r"^admin_blocked$"
    )
)


app.add_handler(
    CallbackQueryHandler(
        approve_user,
        pattern=r"^approve\|"
    )
)


app.add_handler(
    CallbackQueryHandler(
        reject_user,
        pattern=r"^reject\|"
    )
)


# =========================
# GENERAL FILE BUTTONS
# =========================

app.add_handler(
    CallbackQueryHandler(
        handle_callback
    )
)


# =========================
# FILE UPLOAD
# =========================

app.add_handler(
    MessageHandler(
        filters.Document.ALL,
        upload_file
    )
)


# =========================
# TEXT INPUT
# =========================

app.add_handler(
    MessageHandler(
        filters.TEXT
        & ~filters.COMMAND,
        handle_input
    )
)


# =========================
# MAIN
# =========================

async def main():

    print(
        "✅ Bot Started Successfully"
    )

    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    try:

        await asyncio.Event().wait()

    finally:

        print(
            "🛑 Stopping Bot..."
        )

        await app.updater.stop()

        await app.stop()

        await app.shutdown()


# =========================
# RUN BOT
# =========================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "\n🛑 Bot Stopped"
        )