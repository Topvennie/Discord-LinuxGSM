import subprocess
from asyncio import TimeoutError
from typing import List, Optional, Tuple

import discord
from discord.ext import commands


# Class for commands
class Command():

    def __init__(self, name:str, server_command:bool, user:str, command:str, path:str, strip:bool) -> None:
        self.name = name
        self.server_command = server_command
        self.user = user
        self.command = command
        self.path = path
        self.strip = strip
        self.input = self.require_input

    # Determine if command requires input
    def require_input(self) -> bool:
        return "{}" in self.command

    # Check if an argument tries to go to a different directory
    def strip_str(self, msg:str) -> Tuple[bool, Optional[str]]:
        if msg.startswith("./"):
            msg = msg[2:]
        elif msg.startswith("/"):
            msg = msg[1:]
        if msg.endswith("/"):
            msg = msg[:-1]

        if "/"  in msg:
            return False

        return True, msg

    # Send embeds. Can't use one in discordLinusGSM.py because of circular import
    async def send(bot:commands.Bot, channel:discord.TextChannel, description:str, title:str="", delete_after:int=None) -> Optional[discord.Message]:
        embed = discord.Embed(
            title=title,
            description=description,
            colour=bot.embed_colour
        )
        try:
            msg = await channel.send(embed=embed, delete_after=delete_after)
        except discord.errors.Forbidden:
            info = await bot.application_info()
            owner = info.owner
            try:
                await owner.send(f"""I am unable to send embeds in {channel.name}.
                                    Without the proper permissions I'm unable to function properly!""")
            except discord.errors.Forbidden:
                pass
            return None

        return msg

    # Ask for arguments to the user
    async def ask_for_input(self, bot:commands.Bot, channel:discord.TextChannel, author:discord.Member) -> Tuple[bool, Optional[List[str]]]:
        def check(msg):
            return msg.author == author and msg.channel == channel

        await send(bot, channel, f'`{self.name}` requires {self.command.count("{}")} argument(s)\nPlease give them seperated with a space\nIf one of the arguments includes a space then enclose it in __double__ quotes (" ") ', delete_after=60)
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
        except TimeoutError:
            return False

        arguments = []

        msg = msg.content
        while msg.find('"') != -1:
            index_1 = msg.find('"')
            index_2 = msg.find('"', index_1 + 1)
            arguments.push(msg[index_1 + 1:index_2])
            msg = msg.replace(msg[index_1:index_2 + 1], "")

        [arguments.append(x) for x in msg.split(" ")]
        if len(arguments) != self.command.count("{}"):
            return False

        if self.stip:
            args = arguments.copy()
            for arg in args:
                result = self.strip_str(arg)
                if not result[0]:
                    return False
                arguments.append(arg)

        return True, arguments
        
    # Executes a command
    async def execute(self, bot:commands.Bot, channel:discord.TextChannel, author:discord.Member) -> Tuple[bool, Optional[str], Optional[str], Optional[bool]]:
        if self.input:
            input_result = await self.ask_for_input(bot, channel, author)

        if not input_result[0]:
            return False, None, None, True

        # Formats the command
        command = self.command
        for input in input_result[1]:
            command.replace("{}", f'"{input}"', 1)

        if self.server_command:
            if self.user == "":
                command_array = [f"{self.path} {self.command}"]
            else:
                command_array = ["su", "-c", f"{self.path} {self.command}", "-", self.user]
        else:
            if self.user == "":
                command_array = [f"(cd {self.path} && {self.command})"]
            else:
                command_array = ["su", "-c", f"(cd {self.path} && {self.command})", self.user]

        try:
            result = subprocess.run(command_array, capture_output=True, text=True)
        except FileNotFoundError:
            return False, "", f"`{' '.join(command_array)}` could not be executed\nCheck if the file location is right"
        return result.returncode == 0, result.stdout, result.stderr
