from datetime import datetime
import json


# Prints formatted message to the console
def print_to_console(message:str) -> None:
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S: ") + message)


# Terminates the process
def exit(message:str) -> None:
    print_to_console(message)
    print_to_console("Fatal Error, Bot Terminated.\nLook at the github page https://github.com/Topvennie/Discord-LinuxGSM if you need help.")
    raise SystemExit(1)


# Generic function to read a json file
def read_file(file_location:str) -> dict:
    try:
        with open(file_location) as file:
            data = json.load(file)

    except FileNotFoundError:
        exit(f"Could not find {file_location}. Make sure the file has the right name.")

    return data