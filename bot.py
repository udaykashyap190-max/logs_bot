# =========================================================
# FILE: bot.py
# PART 9E
# =========================================================
import os

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
# IMPORT ENVIRONMENT VARIABLES
# =========================================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = os.getenv('OWNER_ID')

# =========================================================
# BUILD APPLICATION
# =========================================================
app = (
 Application.builder()
 .token(BOT_TOKEN)
 .build()
)
# ... rest of file
