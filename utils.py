import json
from datetime import datetime
from math import floor
from typing import Optional

import discord
from discord.ext import commands


# Prints formatted message to the console
def print_to_console(message:str) -> None:
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S: ") + message)


# Terminates the process
def exit(message:str) -> None:
    print_to_console(message)
    print_to_console("Fatal Error, Bot Terminated.\nLook at the github page https://github.com/Topvennie/Discord-LinuxGSM/wiki if you need help.")
    raise SystemExit(1)


# Generic function to read a json file
def read_file(file_location:str) -> dict:
    try:
        with open(file_location) as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                exit(f"There's a json format error in {file_location}")

    except FileNotFoundError:
        exit(f"Could not find {file_location}. Make sure the file has the right name.")

    return data

# Returns the current unix time
def get_unix_time() -> int:
    return floor((datetime.utcnow() - datetime(year=1970, month=1, day=1)).total_seconds())

# Send embeds
async def send(bot:commands.Bot, channel:discord.TextChannel, description:str, title:str="", footer:str="", delete_after:int=None) -> Optional[discord.Message]:
    embed = discord.Embed(
        title=title,
        description=description,
        colour=bot.embed_colour
    )
    embed.set_footer(text=footer)
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
        return

    return msg
