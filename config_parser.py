import os
from typing import List, Optional, Tuple, Union

from discord import Activity, ActivityType, Color, Game

from command import Command
from server import Server
from utils import exit, print_to_console, read_file


#####################
#  required values  #
#####################


settings_required_values = ["prefix", "token", "activity type", "activity text", "server", "head admin", "admin", "moderator", "embed colour"]
commands_required_values = ["server_command", "command", "require_path", "strip_user_input"]
server_required_values = ["name", "user", "path", "head admin", "admin", "moderator", "commands"]
server_commands_requires_values = ["name", "user", "command"]

forbidden_server_names = ["restart", "reload", "refresh", "settings", "setting", "setprefix", "set_prefix", "setactivity", "set_activity", "set_activity_type", "set_activity_text", "set_activitytype", "set_activitytext", "setactivitytype", 
                        "setactivitytext", "setheadadmin", "set_head_admin", "set_headadmin", "setadmin", "set_admin", "setmoderator", "set_moderator", "setembedcolour", "set_embed_colour", "set_embed_color", "set_embedcolour", "set_embedcolor", 
                        "setembedcolor", "set_colour", "set_color", "setcolour", "setcolor", "servers"]


###########
#  utils  #
###########


# Checks if a dict has all the required keys
def check_required_values(required_values:List[str], data:dict) -> Tuple[bool, str]:
    data_keys = data.keys()

    for value in required_values:
        if value not in data_keys:
            return False, value

    return True, ""

# Checks if the id could be real. More checks follow later
def check_id_exists(id:Union[str, int]) -> int:
    if isinstance(id, str):
        if id == "":
            return 0
        if not id.isdigit():
            exit(f"'{id}' isn't valid role id. Leave empty or set to 0 to disable.")
    else:
        id = str(id)

    if len(id) != 18 and id != "0":
        exit(f"'{id}' isn't valid role id. Leave empty or set to 0 to disable.")     
        
    return int(id)

# Checks if something can represent a bool
def check_bool(data:Union[str, bool]) -> Tuple[bool, Optional[bool]]:
    if isinstance(data, bool):
        return True, data

    if isinstance(data, str):
        if data.lower() == "true":
            return True, True

        if data.lower() == "false":
            return True, False

    if isinstance(data, int):
        if data == 1:
            return True, True

        if data == 0:
            return True, False

    return False, None


###################
#  settings.json  #
###################


# Parses the settings file
def parse_settings() -> Tuple[str, str, Activity, int, int, int, int, Color]:
    data = read_file("./configs/settings.json")

    check_values = check_required_values(settings_required_values, data)
    if not check_values[0]:
        exit(f"'{check_values[1]}' was not in ./configs/settings.json. Look at the github page to see a template for the settings file.")

    # Bot information
    prefix = data["prefix"]
    token = data["token"]
    activity_type = data["activity type"]
    activity_text = data["activity text"]

    if prefix == "":
        prefix = "!!"

    token_split = token.split(".")
    if len(token) != 59 or len(token_split) != 3:
        exit(f"Invalid bot token. Please refer to the github page on how to get a bot token.")

    activity = None
    if activity_type != "" and activity_text != "":
        if activity_type == "playing":
            activity = Game(name=activity_text)
        elif activity_type == "watching":
            activity = Activity(type=ActivityType.watching, name=activity_text)
        elif activity_type == "listening":
            activity = Activity(type=ActivityType.listening, name=activity_text)
        else:
            exit("Invalid activity type! Can only be 'playing', 'watching' or 'listening'. To disable leave empty.")
    elif activity_type != "" and activity_text == "":
        exit("'activity_text' is required when specifying an activity_type. To disable leave both empty.")

    # Optional server or role restrictions
    guild = check_id_exists(data["server"])
    head_admin = check_id_exists(data["head admin"])
    admin = check_id_exists(data["admin"])
    moderator = check_id_exists(data["moderator"])

    # Only allow staff roles if a guild is specified
    if guild == 0:
        exit("A server id is required.")

    if head_admin != 0 and admin != 0 and moderator != 0:
        exit(f"You need to set at least one staff role.")

    # embed colour
    embed_colour_data = data["embed colour"]

    if embed_colour_data == []:
        embed_colour = Color.from_rgb(255, 255, 255)
    else:
        embed_colour = []
        exit_phrase = "Embed colour consists of three integers between 0 and 255, seperated by a comma ','. Look at the github page for more information."
        if len(embed_colour_data) != 3:
            exit(exit_phrase)
        for number in embed_colour_data:
            if isinstance(number, str):
                if not number.isdigit():
                    exit(exit_phrase)
                else:
                    number = int(number)
            
            if not 0 <= number <= 255:
                exit(exit_phrase)
            embed_colour.append(number)
        
        embed_colour = Color.from_rgb(embed_colour[0], embed_colour[1], embed_colour[2])

    return prefix, token, activity, guild, head_admin, admin, moderator, embed_colour

# Parses the commands file
def parse_commands() -> dict:
    data = read_file("./configs/commands.json")

    all_commands = {}

    for command in data:
        # Has all the values
        check_values = check_required_values(commands_required_values, data[command])
        if not check_values[0]:
            print_to_console(f"'{command}' will not be added as a command because it doesn't have a value for '{check_values[1]}'.")
            continue

        # TODO Shorten 
        server_command = check_bool(data[command]["server_command"])
        if server_command[1]:
            print_to_console(f"'{command}' will not be added as the option 'server_command' is not a boolean.")
            continue
        server_command = server_command[1]

        require_path = check_bool(data[command]["require_path"])
        if require_path[1]:
            print_to_console(f"'{command}' will not be added as the option 'require_path' is not a boolean.")
            continue
        require_path = require_path[1]

        strip_user_input = check_bool(data[command]["strip_user_input"])
        if strip_user_input[1]:
            print_to_console(f"'{command}' will not be added as the option 'strip_user_input' is not a boolean.")
            continue
        strip_user_input = strip_user_input[1]

        command = data[command]["command"]

        all_commands[command] = [server_command, command, require_path, strip_user_input]
        
    return all_commands

# Parses the servers file
def parse_servers(template_commands:dict) -> List[Server]:
    data = read_file("./configs/servers.json")
    all_servers = []

    for server_name in data:
        # Check for required values
        check_values = check_required_values(server_required_values, data[server_name])
        if not check_values[0]:
            print_to_console(f"'{server_name}' will not be added as it does not have '{check_values[1]}'.")
            continue

        server_name = data[server_name]["name"]
        server_user = data[server_name]["user"]
        server_path = data[server_name]["path"]

        # Check for forbidden server names
        if server_name in forbidden_server_names:
            print_to_console(f"'{server_name}' will not be added as it's name is the same as one of the built in commands.")
            return

        # Basic checks for the file
        if not os.path.exists(server_path):
            print_to_console(f"'{server_name}' will not be added as the given path '{server_path}' does not exists.")
            continue

        if not os.access(server_path, os.X_OK):
            print_to_console(f"'{server_name}' will not be added as the given path '{server_path}' is not executable.")
            continue

        # No duplicates allowed
        for s in all_servers:
            if s.name == server_name:
                print_to_console(f"'{server_name}' will not be added as there's already another server with that name.")
                continue

        server = Server(server_name, server_user, server_path)

        head_admin_commands = data[server_name]["head_admin"]
        admin_commands = data[server_name]["admin"]
        moderator_commands = data[server_name]["moderator"]

        has_commands = False
        for command_data in data[server_name]["commands"]:
            check_values = check_required_values(server_commands_requires_values, data[server_name]["commands"][command_data])
            if not check_values[0]:
                print_to_console(f"'{command_data}' will not be added to '{server_name}' as it does not have '{check_values[1]}'")
                continue

            if data[server_name]["commands"][command_data]["command"] not in template_commands:
                print_to_console(f"'{command_data}' will not be added to '{server_name}' as the command is not in commands.json")
                continue

            command_name = data[server_name]["commands"][command_data]["name"]
            command_user = data[server_name]["commands"][command_data]["user"]

            if template_commands[command_data][2]:
                command_path = data[server_name]["commands"][command_data]["path"]
                # Format path if it's a relative path
                if command_path.startswith("./"):
                    command_path = server_path[:server_path.rfind("/")] + command_path[1:]
            else:
                command_path = server_path

            command = Command(command_name, data[server_name]["commands"][command_data]["command"], command_user, template_commands[command_data][1], command_path, template_commands[command_data][3])

            if command_name in head_admin_commands:
                server.add_head_admin_command(command)
            elif command_name in admin_commands:
                server.add_admin_command(command)
            elif command_name in moderator_commands:
                server.add_moderator_command(command)

            if not has_commands:
                has_commands = True

        if not has_commands:
            print_to_console(f"'{server_name}' will not be added as it doesn't have any valid commands.")
            continue

        all_servers.append(server)

    if len(all_servers) == 0:
        exit("There are no servers with any valid commands.")

    return all_servers