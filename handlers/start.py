# =========================================================
# FILE: handlers/start.py
# PART 9F
# =========================================================

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ContextTypes
)


def get_main_keyboard():

    return InlineKeyboardMarkup([

        [

            InlineKeyboardButton(

                "📂 My Files",

                callback_data="my_files"

            )

        ],

        [

            InlineKeyboardButton(

                "📤 Upload File",

                callback_data="upload"

            )

        ]

    ])
