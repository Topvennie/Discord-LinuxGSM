from typing import Optional

import discord
from discord.ext import commands

from config_parser import parse_commands, parse_servers, parse_settings
from utils import print_to_console


###############
#  Bot Utils  #
###############


# Returns the bot prefix
def get_prefix(bot:commands.Bot, message:discord.Message) -> str:
    return bot.prefix

# Make bot
def make_bot(settings_data:dict, servers_data:dict) -> commands.Bot:
    bot = commands.Bot(
        command_prefix=get_prefix,
        intents=discord.Intents.default(),
        activity=settings_data[2]
    )

    set_bot_variables(settings_data, servers_data)

    bot.remove_command("help")
    try:
        bot.load_extension("./cogs/settings")
        bot.load_extension("./cogs/commands")
    except (commands.ExtensionNotFound, commands.ExtensionFailed) as error:
        exit(f"Failed to load {error.name}. Make sure you have the latest version from the github.")

# Set bot variables
def set_bot_variables(settings_data:dict, servers_data:dict) -> None:
    bot.prefix = settings_data[0]
    bot.guild = settings_data[3]
    bot.head_admin = settings_data[4]
    bot.admin = settings_data[5]
    bot.moderator = settings_data[6]
    bot.embed_colour = settings_data[7]
    bot.servers = servers_data

# Send embeds
async def send(channel:discord.TextChannel, description:str, title:str="", delete_after:int=None) -> Optional[discord.Message]:
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


#####################
#  Start of script  #
#####################


# Settings
print_to_console("1/5 Parsing the settings file...")
settings_data = parse_settings()

# Commands
print_to_console("2/5 Parsing the commands file...")
commands_data = parse_commands()

# Servers
print_to_console("3/5 Parsing the servers file...")
servers_data = parse_servers(commands_data)

# Making the bot
print_to_console("4/5 Making the bot...")
bot = make_bot(settings_data, servers_data)


##############################
#  Bot Commands / Listeners  #
##############################


# Global guild check
@bot.check
async def right_guild(ctx) -> bool:
    return ctx.guild.id == bot.guild

# Reloads both cogs
@bot.command(name="restart", aliases=["reload"])
async def _restart(ctx) -> None:
    msg = await send(ctx, "Reloading the bot...")

    bot.unload_extension("./cogs/settings")
    bot.unload_extension("./cogs/commands")

    settings_data = parse_settings()
    commands_data = parse_commands()
    servers_data = parse_servers(commands_data)

    set_bot_variables(settings_data, servers_data)

    try:
        bot.load_extension("./cogs/settings")
        bot.load_extension("./cogs/commands")
    except commands.ExtensionFailed as error:
        await msg.edit(embed=discord.Embed(description="Failed to reload the bot\nPlease look at the console to see what went wrong", color=bot.color))
        exit(f"Failed to reload '{error.name}' because '{error.original}'")

    await msg.edit(embed=discord.Embed(description="Reloaded bot", color=bot.color))

# Refreshes the server list
@bot.command(name="refresh")
async def _refresh(ctx) -> None:
    msg = await send(ctx, "Refreshing all servers...")

    bot.unload_extension("./cogs/commands")

    commands_data = parse_commands()
    servers_data = parse_servers(commands_data)

    bot.servers = servers_data

    try:
        bot.load_extension("./cogs/commands")
    except commands.ExtensionFailed as error:
        await msg.edit(embed=discord.Embed(description="Failed to refresh the servers\nPlease look at the console to get more information", color=bot.color))
        exit(f"Failed to refresh the servers because '{error.original}'")
    
    await msg.edit(embed=discord.Embed(description="Refreshed servers", color=bot.color))

# Ignore all errors
@bot.event
async def on_command_error(ctx, error) -> None:
    print_to_console(f"An error just occurred: {error}")


#############
#  Run Bot  #
#############


# Starting the bot
print_to_console("5/5 Starting the bot...")

try:
    bot.run(settings_data[1])
except discord.errors.LoginFailure:
    exit(f"The token '{settings_data[1]}' is invalid.")
