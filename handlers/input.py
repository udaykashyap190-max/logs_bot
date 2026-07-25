import subprocess
import re

from telegram import Update

from telegram.ext import (
    ContextTypes
)

from core.auth import has_access

from core.process import (
    send_input,
    is_running
)


# =========================
# HANDLE TEXT INPUT
# =========================

async def handle_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    message = update.message


    if user is None or message is None:

        return


    # =========================
    # ACCESS CHECK
    # =========================

    if not has_access(user.id):

        return


    text = message.text


    if not text:

        return


    # =========================
    # MODULE INSTALL MODE
    # =========================

    module_file = context.user_data.get(

        "module_install_file"

    )


    if module_file:

        # Only allow normal Python package names.
        # This prevents arbitrary shell commands.

        if not re.fullmatch(

            r"[A-Za-z0-9_.-]+",

            text.strip()

        ):

            await message.reply_text(

                "❌ Invalid package name.\n\n"

                "Please send a valid Python "
                "package name, for example:\n"

                "`requests`",

                parse_mode="Markdown"

            )

            return


        package = text.strip()


        await message.reply_text(

            f"📦 Installing `{package}`...\n\n"
            f"Please wait.",

            parse_mode="Markdown"

        )


        try:

            result = subprocess.run(

                [

                    "python",

                    "-m",

                    "pip",

                    "install",

                    package

                ],

                capture_output=True,

                text=True,

                timeout=120

            )


            if result.returncode == 0:

                output = result.stdout

                if len(output) > 2500:

                    output = output[-2500:]


                await message.reply_text(

                    f"✅ Module installed successfully!\n\n"

                    f"📦 Package: `{package}`\n\n"

                    f"```text\n"
                    f"{output}\n"
                    f"```",

                    parse_mode="Markdown"

                )


            else:

                error = result.stderr

                if len(error) > 3000:

                    error = error[-3000:]


                await message.reply_text(

                    f"❌ Failed to install `{package}`.\n\n"

                    f"```text\n"
                    f"{error}\n"
                    f"```",

                    parse_mode="Markdown"

                )


        except subprocess.TimeoutExpired:

            await message.reply_text(

                "⏱️ Installation timed out.\n\n"
                "The package may be too large "
                "or unavailable."

            )


        except Exception as e:

            await message.reply_text(

                f"❌ Installation error:\n\n"
                f"{e}"

            )


        # Clear install mode

        context.user_data.pop(

            "module_install_file",

            None

        )


        return


    # =========================
    # NORMAL PROCESS INPUT
    # =========================

    filename = context.user_data.get(

        "active_file"

    )


    if not filename:

        await message.reply_text(

            "ℹ️ No file is selected "
            "for input.\n\n"

            "Click ⌨️ Send Input on "
            "the file you want to control."

        )

        return


    if not is_running(filename):

        await message.reply_text(

            f"❌ `{filename}` is not running.",

            parse_mode="Markdown"

        )

        return


    # =========================
    # SEND INPUT
    # =========================

    success, result = send_input(

        filename,

        text

    )


    if success:

        await message.reply_text(

            f"✅ Input sent to `{filename}`.",

            parse_mode="Markdown"

        )

    else:

        await message.reply_text(

            result

        )
