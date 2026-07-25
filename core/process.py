# =========================================================
# FILE: core/process.py
# PART 9D
# Railway / Linux Compatible Process Manager
# =========================================================

import os
import sys
import subprocess
import threading
import queue
import time
import signal


# =========================================================
# FOLDERS
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
# RUNNING PROCESSES
# =========================================================

RUNNING_PROCESSES = {}


# =========================================================
# OUTPUT QUEUES
# =========================================================

PROCESS_OUTPUTS = {}


# =========================================================
# INPUT QUEUES
# =========================================================

PROCESS_INPUTS = {}


# =========================================================
# LOCK
# =========================================================

PROCESS_LOCK = threading.RLock()


# =========================================================
# LOG PATH
# =========================================================

def get_log_path(
    filename
):

    safe_name = os.path.basename(
        filename
    )

    return os.path.join(

        LOG_FOLDER,

        safe_name + ".log"

    )


# =========================================================
# FILE PATH
# =========================================================

def get_file_path(
    filename
):

    safe_name = os.path.basename(
        filename
    )

    return os.path.abspath(

        os.path.join(

            UPLOAD_FOLDER,

            safe_name

        )

    )


# =========================================================
# WRITE LOG
# =========================================================

def write_log(
    filename,
    text
):

    logpath = get_log_path(
        filename
    )

    try:

        with open(

            logpath,

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
    filename
):

    filename = os.path.basename(
        filename
    )


    # -----------------------------------------------------
    # CHECK EXISTING PROCESS
    # -----------------------------------------------------

    with PROCESS_LOCK:

        if filename in RUNNING_PROCESSES:

            existing = RUNNING_PROCESSES[
                filename
            ]

            process = existing.get(
                "process"
            )


            if process is not None:

                if process.poll() is None:

                    return (

                        False,

                        "⚠️ This file is already running."

                    )


            cleanup_process(
                filename
            )


    # -----------------------------------------------------
    # FILE PATH
    # -----------------------------------------------------

    filepath = get_file_path(
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
    # ONLY PYTHON FILES
    # -----------------------------------------------------

    if not filename.lower().endswith(
        ".py"
    ):

        return (

            False,

            "❌ Only Python files are supported."

        )


    # -----------------------------------------------------
    # LOG PATH
    # -----------------------------------------------------

    logpath = get_log_path(
        filename
    )


    # -----------------------------------------------------
    # START LOG
    # -----------------------------------------------------

    write_log(

        filename,

        "\n\n"
        "========================================\n"
        f"STARTING FILE: {filename}\n"
        f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        "========================================\n"

    )


    # =====================================================
    # WINDOWS / LINUX CREATION FLAGS
    # =====================================================

    creationflags = 0


    if os.name == "nt":

        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP
        )


    # =====================================================
    # START SUBPROCESS
    # =====================================================

    try:

        process = subprocess.Popen(

            [

                sys.executable,

                "-u",

                filepath

            ],

            cwd=os.path.dirname(
                filepath
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

            filename,

            "\n❌ FAILED TO START PROCESS\n"

            f"{str(e)}\n"

        )


        return (

            False,

            f"❌ Error starting process:\n{e}"

        )


    # =====================================================
    # CREATE QUEUES
    # =====================================================

    PROCESS_OUTPUTS[
        filename
    ] = queue.Queue()


    PROCESS_INPUTS[
        filename
    ] = queue.Queue()


    # =====================================================
    # STORE PROCESS
    # =====================================================

    with PROCESS_LOCK:

        RUNNING_PROCESSES[
            filename
        ] = {

            "process":
            process,

            "logpath":
            logpath,

            "last_output":
            "",

            "waiting_for_input":
            False,

            "started_at":
            time.time()

        }


    # =====================================================
    # OUTPUT THREAD
    # =====================================================

    output_thread = threading.Thread(

        target=
        read_process_output,

        args=(

            filename,

            process,

            logpath

        ),

        daemon=True

    )


    output_thread.start()


    # =====================================================
    # INPUT THREAD
    # =====================================================

    input_thread = threading.Thread(

        target=
        write_process_input,

        args=(

            filename,

            process

        ),

        daemon=True

    )


    input_thread.start()


    return (

        True,

        "✅ Process started successfully."

    )


# =========================================================
# READ PROCESS OUTPUT
# =========================================================

def read_process_output(

    filename,

    process,

    logpath

):

    try:

        while True:

            # -------------------------------------------------
            # READ LINE
            # -------------------------------------------------

            line = process.stdout.readline()


            # -------------------------------------------------
            # PROCESS CLOSED
            # -------------------------------------------------

            if line == "":

                if process.poll() is not None:

                    break


                time.sleep(
                    0.05
                )

                continue


            # -------------------------------------------------
            # CLEAN OUTPUT
            # -------------------------------------------------

            output = line


            # -------------------------------------------------
            # SAVE LAST OUTPUT
            # -------------------------------------------------

            if filename in RUNNING_PROCESSES:

                RUNNING_PROCESSES[
                    filename
                ][
                    "last_output"
                ] = output


            # -------------------------------------------------
            # ADD TO OUTPUT QUEUE
            # -------------------------------------------------

            if filename in PROCESS_OUTPUTS:

                PROCESS_OUTPUTS[
                    filename
                ].put(
                    output
                )


            # -------------------------------------------------
            # WRITE TO LOG
            # -------------------------------------------------

            try:

                with open(

                    logpath,

                    "a",

                    encoding="utf-8",

                    errors="replace"

                ) as log:

                    log.write(
                        output
                    )

                    log.flush()


            except Exception:

                pass


            # -------------------------------------------------
            # DETECT COMMON INPUT PROMPTS
            # -------------------------------------------------

            lower_output = (
                output
                .strip()
                .lower()
            )


            input_words = [

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

                "proxy url",

                "choice",

                "select",

                "year",

                "post",

                "number",

                "id:"

            ]


            waiting = any(

                word in lower_output

                for word in input_words

            )


            if filename in RUNNING_PROCESSES:

                RUNNING_PROCESSES[
                    filename
                ][
                    "waiting_for_input"
                ] = waiting


    except Exception as e:

        write_log(

            filename,

            "\n❌ OUTPUT READER ERROR:\n"

            f"{str(e)}\n"

        )


    finally:

        # -----------------------------------------------------
        # PROCESS EXIT CODE
        # -----------------------------------------------------

        try:

            return_code = process.poll()


            if return_code is not None:

                write_log(

                    filename,

                    "\n\n"
                    "========================================\n"
                    f"PROCESS EXITED\n"
                    f"EXIT CODE: {return_code}\n"
                    f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    "========================================\n"

                )

        except Exception:

            pass


# =========================================================
# WRITE PROCESS INPUT
# =========================================================

def write_process_input(

    filename,

    process

):

    while True:

        # -----------------------------------------------------
        # PROCESS STOPPED
        # -----------------------------------------------------

        if process.poll() is not None:

            break


        try:

            value = PROCESS_INPUTS[
                filename
            ].get(

                timeout=0.5

            )


        except queue.Empty:

            continue


        except KeyError:

            break


        # -----------------------------------------------------
        # STOP SIGNAL
        # -----------------------------------------------------

        if value is None:

            break


        # -----------------------------------------------------
        # WRITE INPUT
        # -----------------------------------------------------

        try:

            if process.stdin:

                process.stdin.write(

                    str(value)

                    + "\n"

                )

                process.stdin.flush()


            if filename in RUNNING_PROCESSES:

                RUNNING_PROCESSES[
                    filename
                ][
                    "waiting_for_input"
                ] = False


        except Exception as e:

            write_log(

                filename,

                "\n❌ INPUT ERROR:\n"

                f"{str(e)}\n"

            )

            break


# =========================================================
# SEND INPUT
# =========================================================

def send_input(

    filename,

    value

):

    filename = os.path.basename(
        filename
    )


    if filename not in RUNNING_PROCESSES:

        return (

            False,

            "❌ Process is not running."

        )


    process = RUNNING_PROCESSES[
        filename
    ][
        "process"
    ]


    if process.poll() is not None:

        cleanup_process(
            filename
        )


        return (

            False,

            "❌ Process has already stopped."

        )


    try:

        PROCESS_INPUTS[
            filename
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
# GET OUTPUT
# =========================================================

def get_output(

    filename

):

    if filename not in PROCESS_OUTPUTS:

        return ""


    result = []


    try:

        while True:

            result.append(

                PROCESS_OUTPUTS[
                    filename
                ].get_nowait()

            )


    except queue.Empty:

        pass


    return "".join(
        result
    )


# =========================================================
# STOP PROCESS
# =========================================================

def stop_process(

    filename

):

    filename = os.path.basename(
        filename
    )


    if filename not in RUNNING_PROCESSES:

        return (

            False,

            "⚠️ Process is not running."

        )


    process = RUNNING_PROCESSES[
        filename
    ][
        "process"
    ]


    try:

        if process.poll() is None:

            # -------------------------------------------------
            # WINDOWS
            # -------------------------------------------------

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


            # -------------------------------------------------
            # NORMAL TERMINATE
            # -------------------------------------------------

            if process.poll() is None:

                process.terminate()


            # -------------------------------------------------
            # WAIT
            # -------------------------------------------------

            try:

                process.wait(
                    timeout=3
                )

            except subprocess.TimeoutExpired:

                process.kill()


        cleanup_process(

            filename

        )


        write_log(

            filename,

            "\n\n"
            "========================================\n"
            "PROCESS STOPPED BY USER\n"
            f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            "========================================\n"

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

    filename

):

    filename = os.path.basename(
        filename
    )


    if filename in RUNNING_PROCESSES:

        stop_process(

            filename

        )


        time.sleep(
            0.3
        )


    return start_process(

        filename

    )


# =========================================================
# CHECK RUNNING
# =========================================================

def is_running(

    filename

):

    filename = os.path.basename(
        filename
    )


    if filename not in RUNNING_PROCESSES:

        return False


    process = RUNNING_PROCESSES[
        filename
    ][
        "process"
    ]


    if process.poll() is None:

        return True


    cleanup_process(

        filename

    )


    return False


# =========================================================
# CHECK INPUT WAITING
# =========================================================

def is_waiting_for_input(

    filename

):

    filename = os.path.basename(
        filename
    )


    if filename not in RUNNING_PROCESSES:

        return False


    return RUNNING_PROCESSES[
        filename
    ].get(

        "waiting_for_input",

        False

    )


# =========================================================
# CLEANUP PROCESS
# =========================================================

def cleanup_process(

    filename

):

    filename = os.path.basename(
        filename
    )


    with PROCESS_LOCK:

        if filename in RUNNING_PROCESSES:

            try:

                process = RUNNING_PROCESSES[
                    filename
                ][
                    "process"
                ]


                if process.poll() is None:

                    process.terminate()


            except Exception:

                pass


            del RUNNING_PROCESSES[
                filename
            ]


        PROCESS_INPUTS.pop(

            filename,

            None

        )


        PROCESS_OUTPUTS.pop(

            filename,

            None

        )


# =========================================================
# GET LOGS
# =========================================================

def get_logs(

    filename,

    max_chars=3500

):

    filename = os.path.basename(
        filename
    )


    logpath = get_log_path(

        filename

    )


    if not os.path.exists(

        logpath

    ):

        return (

            "📄 No logs available yet."

        )


    try:

        with open(

            logpath,

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

                "… Showing latest logs …\n\n"

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

    filename

):

    filename = os.path.basename(
        filename
    )


    logpath = get_log_path(

        filename

    )


    try:

        with open(

            logpath,

            "w",

            encoding="utf-8"

        ):

            pass


        return True


    except Exception:

        return False
