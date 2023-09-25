################################ IMPORTS ################################
import time                                                            ##
import uuid                                                            ##
import logging                                                         ##
import threading                                                       ##
from colorama import Fore, Style,init                                  ##                                                                            ##
#########################################################################


# Only logs Errors into the file
logging.basicConfig(filename='console.log', level=logging.ERROR)
logging_mutex = threading.Lock()
init(autoreset=True)


def console_output(text: str, msg_type: str = 'INFO', color: str = None, file_path: str = None):
    """
    Outputs a console message with an optional message type, color, and file path.

    Args:
        text (str): The message to display.
        msg_type (str, optional): The type of the message (e.g., INFO, WARNING, ERROR). Defaults to 'INFO'.
        color (str, optional): The color of the message (e.g., Fore.GREEN, Fore.RED). Defaults to None.
        file_path (str, optional): The path to a file to write the message to. Defaults to None.
    """
    colors = {
        'SUCCESS': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'INFO': Fore.WHITE
    }

    if color:
        text_color = color
    elif msg_type in colors:
        text_color = colors[msg_type]
    else:
        text_color = Fore.WHITE

    template = f"{msg_type}: " if msg_type else ""
    text = f"{template}{text}"

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_uuid = uuid.uuid4()
    formatted_text = f"[{timestamp}] (UUID : {log_uuid}) {text}"
    

    with logging_mutex:
        logging.debug(formatted_text)
        if file_path:
            with open(file_path, 'a') as f:
                f.write(f"{formatted_text}\n")
        print(f"{text_color}{formatted_text}{Style.RESET_ALL}")
