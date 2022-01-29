from typing import List, Optional, Tuple

from discord import Member, TextChannel
from discord.ext.commands import Bot

from command import Command


# Class for the different servers
class Server():
    def __init__(self, name:str, path:str) -> None:
        self.name : str = name
        self.path : str = path
        self.head_admin_commands : List[Command] = []
        self.admin_commands : List[Command] = []
        self.moderator_commands : List[Command] = []
        self.all_commands : List[Command] = []

    # Makes sure each command is unique 
    def add_head_admin_command(self, command:Command) -> None:
        if command not in self.admin_commands and command not in self.moderator_commands:
            self.head_admin_commands.append(command)
            self.all_commands.append(command)

    def add_admin_command(self, command:Command) -> None:
        if command not in self.moderator_commands:
            self.admin_commands.append(command)
            self.all_commands.append(command)

    def add_moderator_command(self, command:Command) -> None:
            self.moderator_commands.append(command)
            self.all_commands.append(command)

    # Returns all the commands a head admin can use
    @property
    def head_admin(self) -> List[Command]:
        commands = [x for x in self.head_admin_commands]
        [commands.append(x) for x in self.admin_commands if x not in commands]
        [commands.append(x) for x in self.moderator_commands if x not in commands]

        return commands

    # Returns all the commands an admin can use
    @property
    def admin(self) -> List[Command]:
        commands = [x for x in self.admin_commands]
        [commands.append(x) for x in self.moderator_commands if x not in commands]

        return commands

    # Returns all the commands a moderator can use
    @property
    def moderator(self) -> List[Command]:
        return self.moderator_commands

    # Executes the commands
    async def execute_command(self, bot:Bot, user_command:Command, channel:TextChannel, author:Member) -> Tuple[bool, Optional[str], Optional[str], Optional[bool]]:
        for command in self.all_commands:
            if command == user_command:
                result = await command.execute(bot, channel, author)
                return result

        return False, None, None
