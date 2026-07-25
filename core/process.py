# =========================================================
# FILE: core/process.py
# PART 9F
# User-Specific Process Manager
# =========================================================

import os
import sys
import subprocess
import threading
import queue
import time
import signal


# =========================================================
# DIRECTORIES
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

LOG_FOLDER = os.path.join(
    BASE_DIR,
    "logs"
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    LOG_FOLDER,
    exist_ok=True
)


# =========================================================
# PROCESS STORAGE
#
# KEY:
# (user_id, filename)
# =========================================================

RUNNING_PROCESSES = {}

PROCESS_OUTPUTS = {}

PROCESS_INPUTS = {}

PROCESS_LOCK = threading.RLock()


# =========================================================
# SAFE FILENAME
# =========================================================

def safe_filename(
    filename
):

    return os.path.basename(
        filename
    )


# =========================================================
# PROCESS KEY
# =========================================================

def process_key(
    user_id,
    filename
):

    return (

        int(user_id),

        safe_filename(
            filename
        )

    )


# =========================================================
# USER UPLOAD DIRECTORY
# =========================================================

def get_user_upload_folder(
    user_id
):

    folder = os.path.join(

        UPLOAD_FOLDER,

        str(user_id)

    )

    os.makedirs(

        folder,

        exist_ok=True

    )

    return folder


# =========================================================
# USER LOG DIRECTORY
# =========================================================

def get_user_log_folder(
    user_id
):

    folder = os.path.join(

        LOG_FOLDER,

        str(user_id)

    )

    os.makedirs(

        folder,

        exist_ok=True

    )

    return folder


# =========================================================
# FILE PATH
# =========================================================

def get_file_path(
    user_id,
    filename
):

    return os.path.join(

        get_user_upload_folder(
            user_id
        ),

        safe_filename(
            filename
        )

    )


# =========================================================
# LOG PATH
# =========================================================

def get_log_path(
    user_id,
    filename
):

    return os.path.join(

        get_user_log_folder(
            user_id
        ),

        safe_filename(
            filename
        ) + ".log"

    )


# =========================================================
# WRITE LOG
# =========================================================

def write_log(
    user_id,
    filename,
    text
):

    path = get_log_path(

        user_id,

        filename

    )


    try:

        with open(

            path,

            "a",

            encoding="utf-8",

            errors="replace"

        ) as log:

            log.write(

                text

            )

            log.flush()


        return True


    except Exception:

        return False


# =========================================================
# START PROCESS
# =========================================================

def start_process(
    user_id,
    filename
):

    filename = safe_filename(
        filename
    )

    key = process_key(

        user_id,

        filename

    )


    # -----------------------------------------------------
    # CHECK ALREADY RUNNING
    # -----------------------------------------------------

    with PROCESS_LOCK:

        if key in RUNNING_PROCESSES:

            existing = RUNNING_PROCESSES[
                key
            ]

            process = existing.get(
                "process"
            )


            if (

                process is not None

                and

                process.poll() is None

            ):

                return (

                    False,

                    "⚠️ This file is already running."

                )


            cleanup_process(

                user_id,

                filename

            )


    # -----------------------------------------------------
    # FILE PATH
    # -----------------------------------------------------

    filepath = get_file_path(

        user_id,

        filename

    )


    if not os.path.isfile(
        filepath
    ):

        return (

            False,

            "❌ File not found."

        )


    # -----------------------------------------------------
    # PYTHON FILE CHECK
    # -----------------------------------------------------

    if not filename.lower().endswith(
        ".py"
    ):

        return (

            False,

            "❌ Only Python files are supported."

        )


    # -----------------------------------------------------
    # LOG
    # -----------------------------------------------------

    write_log(

        user_id,

        filename,

        "\n\n"
        "========================================\n"
        f"STARTING FILE: {filename}\n"
        f"USER ID: {user_id}\n"
        f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "========================================\n"

    )


    # =====================================================
    # CREATION FLAGS
    # =====================================================

    creationflags = 0


    if os.name == "nt":

        creationflags = (

            subprocess.CREATE_NEW_PROCESS_GROUP

        )


    # =====================================================
    # START PYTHON PROCESS
    # =====================================================

    try:

        process = subprocess.Popen(

            [

                sys.executable,

                "-u",

                filepath

            ],

            cwd=get_user_upload_folder(
                user_id
            ),

            stdin=subprocess.PIPE,

            stdout=subprocess.PIPE,

            stderr=subprocess.STDOUT,

            text=True,

            bufsize=1,

            universal_newlines=True,

            creationflags=creationflags

        )


    except Exception as e:

        write_log(

            user_id,

            filename,

            "\n❌ FAILED TO START PROCESS\n"

            f"{str(e)}\n"

        )


        return (

            False,

            f"❌ Error starting process:\n{e}"

        )


    # =====================================================
    # QUEUES
    # =====================================================

    PROCESS_OUTPUTS[
        key
    ] = queue.Queue()


    PROCESS_INPUTS[
        key
    ] = queue.Queue()


    # =====================================================
    # STORE PROCESS
    # =====================================================

    with PROCESS_LOCK:

        RUNNING_PROCESSES[
            key
        ] = {

            "process":
            process,

            "started_at":
            time.time(),

            "waiting_for_input":
            False,

            "last_output":
            ""

        }


    # =====================================================
    # OUTPUT THREAD
    # =====================================================

    threading.Thread(

        target=
        read_process_output,

        args=(

            user_id,

            filename,

            process

        ),

        daemon=True

    ).start()


    # =====================================================
    # INPUT THREAD
    # =====================================================

    threading.Thread(

        target=
        write_process_input,

        args=(

            user_id,

            filename,

            process

        ),

        daemon=True

    ).start()


    return (

        True,

        "✅ Process started successfully."

    )


# =========================================================
# READ OUTPUT
# =========================================================

def read_process_output(

    user_id,

    filename,

    process

):

    key = process_key(

        user_id,

        filename

    )


    try:

        while True:

            line = process.stdout.readline()


            if line == "":

                if process.poll() is not None:

                    break


                time.sleep(
                    0.05
                )

                continue


            # -------------------------------------------------
            # SAVE LAST OUTPUT
            # -------------------------------------------------

            if key in RUNNING_PROCESSES:

                RUNNING_PROCESSES[
                    key
                ][
                    "last_output"
                ] = line


            # -------------------------------------------------
            # OUTPUT QUEUE
            # -------------------------------------------------

            if key in PROCESS_OUTPUTS:

                PROCESS_OUTPUTS[
                    key
                ].put(

                    line

                )


            # -------------------------------------------------
            # LOG
            # -------------------------------------------------

            write_log(

                user_id,

                filename,

                line

            )


            # -------------------------------------------------
            # INPUT DETECTION
            # -------------------------------------------------

            output = line.strip().lower()


            keywords = [

                "enter",

                "input",

                "api key",

                "apikey",

                "chat id",

                "chat_id",

                "token",

                "username",

                "password",

                "email",

                "phone",

                "proxy",

                "choice",

                "select",

                "year",

                "post",

                "number",

                "id:"

            ]


            waiting = any(

                word in output

                for word in keywords

            )


            if key in RUNNING_PROCESSES:

                RUNNING_PROCESSES[
                    key
                ][
                    "waiting_for_input"
                ] = waiting


    except Exception as e:

        write_log(

            user_id,

            filename,

            "\n❌ OUTPUT ERROR:\n"

            f"{str(e)}\n"

        )


    finally:

        try:

            exit_code = process.poll()


            write_log(

                user_id,

                filename,

                "\n\n"
                "========================================\n"
                "PROCESS EXITED\n"
                f"EXIT CODE: {exit_code}\n"
                f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                "========================================\n"

            )


        except Exception:

            pass


# =========================================================
# WRITE INPUT
# =========================================================

def write_process_input(

    user_id,

    filename,

    process

):

    key = process_key(

        user_id,

        filename

    )


    while True:

        if process.poll() is not None:

            break


        try:

            value = PROCESS_INPUTS[
                key
            ].get(

                timeout=0.5

            )


        except queue.Empty:

            continue


        except KeyError:

            break


        if value is None:

            break


        try:

            if process.stdin:

                process.stdin.write(

                    str(value)

                    + "\n"

                )

                process.stdin.flush()


            if key in RUNNING_PROCESSES:

                RUNNING_PROCESSES[
                    key
                ][
                    "waiting_for_input"
                ] = False


        except Exception as e:

            write_log(

                user_id,

                filename,

                "\n❌ INPUT ERROR:\n"

                f"{str(e)}\n"

            )

            break


# =========================================================
# SEND INPUT
# =========================================================

def send_input(

    user_id,

    filename,

    value

):

    key = process_key(

        user_id,

        filename

    )


    if key not in RUNNING_PROCESSES:

        return (

            False,

            "❌ Process is not running."

        )


    process = RUNNING_PROCESSES[
        key
    ][
        "process"
    ]


    if process.poll() is not None:

        cleanup_process(

            user_id,

            filename

        )


        return (

            False,

            "❌ Process has already stopped."

        )


    try:

        PROCESS_INPUTS[
            key
        ].put(

            value

        )


        return (

            True,

            "✅ Input sent."

        )


    except Exception as e:

        return (

            False,

            f"❌ Failed to send input:\n{e}"

        )


# =========================================================
# STOP PROCESS
# =========================================================

def stop_process(

    user_id,

    filename

):

    filename = safe_filename(
        filename
    )

    key = process_key(

        user_id,

        filename

    )


    if key not in RUNNING_PROCESSES:

        return (

            False,

            "⚠️ Process is not running."

        )


    process = RUNNING_PROCESSES[
        key
    ][
        "process"
    ]


    try:

        if process.poll() is None:

            if os.name == "nt":

                try:

                    process.send_signal(

                        signal.CTRL_BREAK_EVENT

                    )

                    time.sleep(
                        0.5
                    )

                except Exception:

                    pass


            if process.poll() is None:

                process.terminate()


            try:

                process.wait(

                    timeout=3

                )

            except subprocess.TimeoutExpired:

                process.kill()


        write_log(

            user_id,

            filename,

            "\n\n"
            "========================================\n"
            "PROCESS STOPPED BY USER\n"
            f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            "========================================\n"

        )


        cleanup_process(

            user_id,

            filename

        )


        return (

            True,

            "⏹️ Process stopped successfully."

        )


    except Exception as e:

        return (

            False,

            f"❌ Error stopping process:\n{e}"

        )


# =========================================================
# RESTART PROCESS
# =========================================================

def restart_process(

    user_id,

    filename

):

    stop_process(

        user_id,

        filename

    )


    time.sleep(
        0.3
    )


    return start_process(

        user_id,

        filename

    )


# =========================================================
# IS RUNNING
# =========================================================

def is_running(

    user_id,

    filename

):

    key = process_key(

        user_id,

        filename

    )


    if key not in RUNNING_PROCESSES:

        return False


    process = RUNNING_PROCESSES[
        key
    ][
        "process"
    ]


    if process.poll() is None:

        return True


    cleanup_process(

        user_id,

        filename

    )


    return False


# =========================================================
# WAITING FOR INPUT
# =========================================================

def is_waiting_for_input(

    user_id,

    filename

):

    key = process_key(

        user_id,

        filename

    )


    if key not in RUNNING_PROCESSES:

        return False


    return RUNNING_PROCESSES[
        key
    ].get(

        "waiting_for_input",

        False

    )


# =========================================================
# GET LOGS
# =========================================================

def get_logs(

    user_id,

    filename,

    max_chars=3500

):

    path = get_log_path(

        user_id,

        filename

    )


    if not os.path.exists(
        path
    ):

        return (
            "📄 No logs available yet."
        )


    try:

        with open(

            path,

            "r",

            encoding="utf-8",

            errors="replace"

        ) as log:

            content = log.read()


        if not content.strip():

            return (
                "📄 Log file is empty."
            )


        if len(content) > max_chars:

            content = (

                "… Latest logs …\n\n"

                + content[
                    -max_chars:
                ]

            )


        return content


    except Exception as e:

        return (

            "❌ Could not read logs:\n"

            + str(e)

        )


# =========================================================
# CLEAR LOGS
# =========================================================

def clear_logs(

    user_id,

    filename

):

    path = get_log_path(

        user_id,

        filename

    )


    try:

        with open(

            path,

            "w",

            encoding="utf-8"

        ):

            pass


        return True


    except Exception:

        return False


# =========================================================
# CLEANUP
# =========================================================

def cleanup_process(

    user_id,

    filename

):

    key = process_key(

        user_id,

        filename

    )


    with PROCESS_LOCK:

        RUNNING_PROCESSES.pop(

            key,

            None

        )


        PROCESS_INPUTS.pop(

            key,

            None

        )


        PROCESS_OUTPUTS.pop(

            key,

            None

        )


# =========================================================
# GET USER PROCESSES
# =========================================================

def get_user_processes(

    user_id

):

    result = []


    with PROCESS_LOCK:

        for key, data in RUNNING_PROCESSES.items():

            stored_user_id, filename = key


            if stored_user_id == int(
                user_id
            ):

                process = data.get(
                    "process"
                )


                running = (

                    process is not None

                    and

                    process.poll() is None

                )


                result.append({

                    "filename":
                    filename,

                    "running":
                    running,

                    "started_at":
                    data.get(
                        "started_at"
                    ),

                    "waiting_for_input":
                    data.get(
                        "waiting_for_input",
                        False
                    )

                })


    return result
