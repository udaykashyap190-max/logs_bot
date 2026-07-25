import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN

from database import init_db

from handlers.start import start
from handlers.upload import upload_file
from handlers.callback import handle_callback


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Exception while handling update:",
        exc_info=context.error
    )


# =========================================================
# MAIN
# =========================================================

async def main():

    # -----------------------------------------------------
    # Initialize database
    # -----------------------------------------------------

    init_db()

    # -----------------------------------------------------
    # Create Telegram application
    # -----------------------------------------------------

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # COMMANDS
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # -----------------------------------------------------
    # CALLBACK BUTTONS
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            handle_callback
        )
    )

    # -----------------------------------------------------
    # FILE UPLOADS
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            upload_file
        )
    )

    # -----------------------------------------------------
    # ERROR HANDLER
    # -----------------------------------------------------

    app.add_error_handler(
        error_handler
    )

    # -----------------------------------------------------
    # START BOT
    # -----------------------------------------------------

    print(
        "===================================="
    )

    print(
        "🤖 FILE RUNNER BOT"
    )

    print(
        "===================================="
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
        "===================================="
    )

    # -----------------------------------------------------
    # Start polling
    # -----------------------------------------------------

    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    try:

        # Keep bot running
        await asyncio.Event().wait()

    finally:

        # -------------------------------------------------
        # Graceful shutdown
        # -------------------------------------------------

        await app.updater.stop()

        await app.stop()

        await app.shutdown()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "\n🛑 Bot stopped by user."
        )

    except Exception as e:

        print(
            "\n❌ Bot stopped because of an error:"
        )

        print(
            str(e)
        )
