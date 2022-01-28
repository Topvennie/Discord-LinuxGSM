import discord
from discord.ext import commands

from config_parser import parse_commands, parse_servers, parse_settings
from utils import print_to_console, send


###############
#  Bot Utils  #
###############


# Returns the bot prefix
def get_prefix(bot:commands.Bot, message:discord.Message) -> str:
    return bot.prefix

# Make bot
def make_bot(bot:commands.Bot, settings_data:dict, servers_data:dict) -> None:
    set_bot_variables(bot, settings_data, servers_data)

    bot.remove_command("help")
    try:
        bot.load_extension("cogs.settings")
        bot.load_extension("cogs.commands")
    except (commands.ExtensionNotFound, commands.ExtensionFailed) as error:
        exit(f"Failed to load {error.name}. Make sure you have the latest version from the github.")

# Set bot variables
def set_bot_variables(bot:commands.Bot, settings_data:dict, servers_data:dict) -> None:
    bot.prefix = settings_data[0]
    bot.guild = settings_data[3]
    bot.head_admin = settings_data[4]
    bot.admin = settings_data[5]
    bot.moderator = settings_data[6]
    bot.embed_colour = settings_data[7]
    bot.servers = servers_data

# Tries to convert the settings to objects
async def startup_check(bot:commands.Bot) -> None:
    try:
        bot.guild = await bot.fetch_guild(bot.guild)
    except discord.errors.Forbidden:
        bot.guild = None

    if bot.guild is None:
        print_to_console(f"""use the invite link to invite me to the server specified in settings.json
                        After which use the command `{bot.prefix}restart` to restart the bot""")
            
    bot.head_admin = bot.guild.get_role(bot.head_admin)
    bot.admin = bot.guild.get_role(bot.admin)
    bot.moderator = bot.guild.get_role(bot.moderator)


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

bot = commands.Bot(
        command_prefix=get_prefix,
        intents=discord.Intents.default(),
        activity=settings_data[2]
    )

make_bot(bot, settings_data, servers_data)


##############################
#  Bot Commands / Listeners  #
##############################


# Global guild check
@bot.check
async def right_guild(ctx) -> bool:
    return ctx.guild == bot.guild

# Reloads both cogs
@bot.command(name="restart", aliases=["reload"])
async def _restart(ctx) -> None:
    msg = await send(bot, ctx, "Reloading the bot...")

    bot.unload_extension("cogs.settings")
    bot.unload_extension("cogs.commands")

    settings_data = parse_settings()
    commands_data = parse_commands()
    servers_data = parse_servers(commands_data)

    set_bot_variables(bot, settings_data, servers_data)

    try:
        bot.load_extension("cogs.settings")
        bot.load_extension("cogs.commands")
    except commands.ExtensionFailed as error:
        await msg.edit(embed=discord.Embed(description="Failed to reload the bot\nPlease look at the console to see what went wrong", color=bot.embed_colour))
        exit(f"Failed to reload '{error.name}' because '{error.original}'")

    await startup_check(bot)
    await msg.edit(embed=discord.Embed(description="Reloaded bot", color=bot.embed_colour))

# Refreshes the server list
@bot.command(name="refresh")
async def _refresh(ctx) -> None:
    msg = await send(bot, ctx, "Refreshing all servers...")

    bot.unload_extension("cogs.commands")

    commands_data = parse_commands()
    servers_data = parse_servers(commands_data)

    bot.servers = servers_data

    try:
        bot.load_extension("cogs.commands")
    except commands.ExtensionFailed as error:
        await msg.edit(embed=discord.Embed(description="Failed to refresh the servers\nPlease look at the console to get more information", color=bot.embed_colour))
        exit(f"Failed to refresh the servers because '{error.original}'")
    
    await msg.edit(embed=discord.Embed(description=f"Refreshed `{len(servers_data)}` server(s)", color=bot.embed_colour))

# Ignore all errors
@bot.event
async def on_command_error(ctx, error) -> None:
    if isinstance(error, commands.errors.CheckFailure):
        return

    print_to_console(f"An error just occurred: {error}")

# Triggers when the bot is ready and prints some basic information
@bot.event
async def on_ready() -> None:
    await startup_check(bot)

    print("\n\tBot started!")
    print("-"*34)
    print(f"Bot name:\t{bot.user.name}")
    print(f"Bot ID:\t\t{bot.user.id}")
    print(f"Invite link:\thttps://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=10304&scope=bot")
    print("-"*34)
    print(f"Discord server:\t{bot.guild.name if bot.guild is not None else 'Not set'}")
    print(f"Prefix:\t\t{bot.prefix}")
    print(f"Servers:\t{len(bot.servers)}")
    print(f"Head admin:\t{bot.head_admin.name if bot.head_admin is not None else 'Not set'}")
    print(f"Admin:\t\t{bot.admin.name if bot.admin is not None else 'Not set'}")
    print(f"Moderator:\t{bot.moderator.name if bot.moderator is not None else 'Not set'}")
    print("-"*34)
    print("\n")
    print_to_console("Bot is running")


#############
#  Run Bot  #
#############


# Starting the bot
print_to_console("5/5 Starting the bot...")

try:
    bot.run(settings_data[1])
except discord.errors.LoginFailure:
    exit(f"The token '{settings_data[1]}' is invalid.")
