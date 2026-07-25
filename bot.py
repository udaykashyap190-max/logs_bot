import asyncio
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN

from database import init_db

from handlers.start import start
from handlers.upload import upload_file
from handlers.callback import handle_callback


logging.basicConfig(
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
    level=logging.INFO
)


async def error_handler(
    update,
    context
):

    logging.error(
        "Update error:",
        exc_info=context.error
    )


async def main():

    # Initialize database
    init_db()

    # Create bot
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # /start
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Callback buttons
    app.add_handler(
        CallbackQueryHandler(
            handle_callback
        )
    )

    # Uploaded files
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            upload_file
        )
    )

    # Errors
    app.add_error_handler(
        error_handler
    )

    print(
        "================================"
    )

    print(
        "🤖 FILE RUNNER BOT"
    )

    print(
        "================================"
    )

    print(
        "✅ Database Initialized"
    )

    print(
        "✅ Handlers Loaded"
    )

    print(
        "✅ Bot Started Successfully"
    )

    print(
        "================================"
    )

    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    try:

        await asyncio.Event().wait()

    finally:

        await app.updater.stop()

        await app.stop()

        await app.shutdown()


if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "🛑 Bot stopped."
        )
