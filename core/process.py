import os
import sys
import subprocess
import threading
import queue
import time


UPLOAD_FOLDER = "uploads"
LOG_FOLDER = "logs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)


# =========================
# RUNNING PROCESSES
# =========================

RUNNING_PROCESSES = {}

PROCESS_OUTPUTS = {}

PROCESS_INPUTS = {}

PROCESS_LOCK = threading.Lock()


# =========================
# LOG PATH
# =========================

def get_log_path(filename):

    return os.path.join(
        LOG_FOLDER,
        filename + ".log"
    )


# =========================
# START PROCESS
# =========================

def start_process(filename):

    with PROCESS_LOCK:

        if filename in RUNNING_PROCESSES:

            process = RUNNING_PROCESSES[
                filename
            ]["process"]

            if process.poll() is None:

                return (
                    False,
                    "⚠️ This file is already running."
                )

            cleanup_process(filename)


    filepath = os.path.abspath(
        os.path.join(
            UPLOAD_FOLDER,
            filename
        )
    )


    if not os.path.exists(filepath):

        return (
            False,
            "❌ File not found."
        )


    logpath = get_log_path(filename)


    try:

        with open(
            logpath,
            "a",
            encoding="utf-8"
        ) as log:

            log.write(
                "\n\n"
                "========================================\n"
                f"STARTING FILE: {filename}\n"
                "========================================\n"
            )


        # =========================
        # CREATE PROCESS
        # =========================

        process = subprocess.Popen(

            [
                sys.executable,
                "-u",
                filepath
            ],

            cwd=os.path.dirname(filepath),

            stdin=subprocess.PIPE,

            stdout=subprocess.PIPE,

            stderr=subprocess.STDOUT,

            text=True,

            bufsize=1
        )


        PROCESS_OUTPUTS[
            filename
        ] = queue.Queue()


        PROCESS_INPUTS[
            filename
        ] = queue.Queue()


        RUNNING_PROCESSES[
            filename
        ] = {

            "process": process,

            "logpath": logpath,

            "last_output": "",

            "waiting_for_input": False

        }


        # =========================
        # OUTPUT THREAD
        # =========================

        output_thread = threading.Thread(

            target=read_process_output,

            args=(

                filename,

                process,

                logpath

            ),

            daemon=True

        )


        output_thread.start()


        # =========================
        # INPUT THREAD
        # =========================

        input_thread = threading.Thread(

            target=write_process_input,

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


    except Exception as e:

        return (

            False,

            f"❌ Error starting process:\n{e}"

        )


# =========================
# READ OUTPUT
# =========================

def read_process_output(

    filename,

    process,

    logpath

):

    try:

        while process.poll() is None:

            output = process.stdout.readline()


            if not output:

                time.sleep(0.05)

                continue


            # Save logs

            with open(

                logpath,

                "a",

                encoding="utf-8",

                errors="replace"

            ) as log:

                log.write(output)

                log.flush()


            # Save output

            if filename in PROCESS_OUTPUTS:

                PROCESS_OUTPUTS[

                    filename

                ].put(output)


            if filename in RUNNING_PROCESSES:

                RUNNING_PROCESSES[

                    filename

                ][

                    "last_output"

                ] = output


    except Exception:

        pass


    finally:

        if filename in RUNNING_PROCESSES:

            RUNNING_PROCESSES[

                filename

            ][

                "waiting_for_input"

            ] = False


# =========================
# WRITE INPUT
# =========================

def write_process_input(

    filename,

    process

):

    while process.poll() is None:

        try:

            value = PROCESS_INPUTS[

                filename

            ].get(

                timeout=0.5

            )

        except queue.Empty:

            continue


        if value is None:

            break


        try:

            process.stdin.write(

                value + "\n"

            )

            process.stdin.flush()


        except Exception:

            break


# =========================
# SEND INPUT
# =========================

def send_input(

    filename,

    value

):

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

        cleanup_process(filename)

        return (

            False,

            "❌ Process has already stopped."

        )


    try:

        PROCESS_INPUTS[

            filename

        ].put(value)


        RUNNING_PROCESSES[

            filename

        ][

            "waiting_for_input"

        ] = False


        return (

            True,

            "✅ Input sent."

        )


    except Exception as e:

        return (

            False,

            f"❌ Failed to send input:\n{e}"

        )


# =========================
# GET OUTPUT
# =========================

def get_output(filename):

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


    return "".join(result)


# =========================
# STOP PROCESS
# =========================

def stop_process(filename):

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

            process.terminate()


            try:

                process.wait(

                    timeout=5

                )

            except subprocess.TimeoutExpired:

                process.kill()


        cleanup_process(filename)


        return (

            True,

            "⏹️ Process stopped successfully."

        )


    except Exception as e:

        return (

            False,

            f"❌ Error stopping process:\n{e}"

        )


# =========================
# RESTART PROCESS
# =========================

def restart_process(filename):

    if filename in RUNNING_PROCESSES:

        stop_process(filename)


    return start_process(filename)


# =========================
# CHECK RUNNING
# =========================

def is_running(filename):

    if filename not in RUNNING_PROCESSES:

        return False


    process = RUNNING_PROCESSES[

        filename

    ][

        "process"

    ]


    if process.poll() is None:

        return True


    cleanup_process(filename)

    return False


# =========================
# INPUT STATUS
# =========================

def is_waiting_for_input(filename):

    if filename not in RUNNING_PROCESSES:

        return False


    return RUNNING_PROCESSES[

        filename

    ].get(

        "waiting_for_input",

        False

    )


# =========================
# CLEANUP
# =========================

def cleanup_process(filename):

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


# =========================
# GET LOGS
# =========================

def get_logs(

    filename,

    max_chars=3500

):

    logpath = get_log_path(filename)


    if not os.path.exists(logpath):

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

            content = content[

                -max_chars:

            ]


            content = (

                "… Showing latest logs …\n\n"

                + content

            )


        return content


    except Exception as e:

        return (

            "❌ Could not read logs:\n"

            + str(e)

        )


# =========================
# CLEAR LOGS
# =========================

def clear_logs(filename):

    logpath = get_log_path(filename)


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
