import json
from typing import List, Union

import discord
from discord.ext import commands

from ..discordLinuxGSM import send
from ..utils import exit, print_to_console


# Class for all the settings
class Settings(commands.Cog):

    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot


    ############
    #  Checks  #
    ############


    # Tries to convert the settings to objects
    async def startup_check(self) -> None:
        try:
            self.bot.guild = await self.bot.fetch_guild(self.bot.guild)
        except discord.errors.Forbidden:
            self.bot.guild = None

        if self.bot.guild is None:
            exit("A valid server id is required.")
            
        self.bot.head_admin = self.bot.guild.get_role(self.bot.head_admin)
        self.bot.admin = self.bot.guild.get_role(self.bot.admin)
        self.bot.moderator = self.bot.guild.get_role(self.bot.moderator)

        if self.bot.head_admin is None and self.bot.admin is None and self.bot.moderator is None:
            exit("You need at least one valid staff role.")

    # Cog check 
    def cog_check(self, ctx:commands.Context) -> bool:        
        return ctx.guild == self.bot.guild and (self.bot.head_admin in ctx.author.roles or ctx.author.guild_permissions.administrator)


    ###############
    #  Cog Utils  #
    ###############


    # Opens settings file and changes the required setting
    async def change_settings(self, ctx:commands.Context, name:str, value:Union[int, str, List[int, int, int]]) -> bool:
        try:
            with open("./configs/settings.json", "r+") as file:
                data = json.load(file)
                data[name] = value
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
        except FileNotFoundError:
            await send(ctx.channel, """The settings file no longer exists!
                                    You will no longer be able to change any settings.""")
            return False

        return True


    ##############
    #  Commands  #
    ##############


    # Gives overview of all the settings
    @commands.command(name="settings", aliases=["setting"])
    async def _settings(self, ctx:commands.Context) -> None:
        await self.send(ctx, f"""`Prefix:` {self.bot.prefix}
                                `Discord Server:` {self.bot.guild.name}
                                `Servers:` {len(self.bot.servers)}
                                `Head admin:` {self.bot.head_admin.mention if self.bot.head_admin is not None else 'Not set'}
                                `Admin:` {self.bot.admin.mention if self.bot.admin is not None else 'Not set'}
                                `Moderator:` {self.bot.moderator.mention if self.bot.moderator is not None else 'Not set'}""")

    # Sets the prefix
    @commands.command(name="setprefix", aliases=["set_prefix"])
    async def _setprefix(self, ctx:commands.Context, new_prefix:str=None) -> None:
        if new_prefix is None:
            await self.send(ctx, "You forgot to specify the new prefix")
            return

        if new_prefix == self.bot.prefix:
            await self.send(ctx, f"`{new_prefix}` is already your prefix")
            return

        changed_setting = await self.change_settings(ctx, "prefix", new_prefix)

        if changed_setting:
            old_prefix = self.bot.prefix
            self.bot.prefix = new_prefix
            await self.send(ctx.channel, f"""Prefix changed
                                    {old_prefix} `->` {self.bot.prefix}""")

    #Sets a new activity
    @commands.command(name="setactivity", aliases=["set_activity", "set_activity_type", "set_activity_text", "set_activitytype", "set_activitytext", "setactivitytype", "setactivitytext"])
    async def _setactivity(self, ctx:commands.Context, activity_type:str=None, *, activity_text:str=None) -> None:
        error_message = f"""You can set the activity by using the command
                            {self.bot.prefix}setactivity `activity type` `activity text`
                            activity type is either 'playing', 'watching' or 'listening'
                            activity text can be anything you want"""

        if activity_type is None or activity_text is None:
            await self.send(ctx, error_message)
            return

        if activity_type == "playing":
            changed_type = await self.change_settings(ctx, "activity type", activity_type)
            changed_text = await self.change_settings(ctx, "activity text", activity_text)
            activity = discord.Game(name=activity_text)
        elif activity_type == "watching":
            changed_type = await self.change_settings(ctx, "activity type", activity_type)
            changed_text = await self.change_settings(ctx, "activity text", activity_text)
            activity = discord.Activity(type=discord.ActivityType.watching, name=activity_text)
        elif activity_type == "listening":
            changed_type = await self.change_settings(ctx, "activity type", activity_type)
            changed_text = await self.change_settings(ctx, "activity text", activity_text)
            activity = discord.Activity(type=discord.ActivityType.listening, name=activity_text)
        else:
            await self.send(ctx.channel, error_message)
            return

        if changed_type and changed_text:
            async with ctx.typing():
                await self.bot.change_presence(activity=activity)
            await self.send(ctx.channel, "Presence changed")

    # Sets a new head admin role
    @commands.command(name="setheadadmin", aliases=["set_head_admin", "set_headadmin"])
    async def _setheadadmin(self, ctx:commands.Context, role:discord.Role=None) -> None:
        if role is None:
            await self.send(ctx.channel, """You forgot to specify the new head admin role
                                            Specify a new role by either pinging the role or by using it's id or name""")
            return

        if role == self.bot.head_admin:
            await self.send(ctx.channel, f"{role.mention} is already the head admin role")
            return

        if role == self.bot.admin or role == self.bot.moderator:
            await self.send(ctx.channel, f"""Every staff role has to be unique.
                                    Head admins will also have access to the commands for admins and moderators""")
            return

        changed_setting = await self.change_settings(ctx, "head admin", role.id)
        if changed_setting:
            old_role = self.bot.head_admin
            self.bot.head_admin = role
            if old_role is None:
                await self.send(ctx, f"Head admin role set to {self.bot.head_admin.mention}")
            else:
                await self.send(ctx, f"""Head admin role changed
                                                {old_role.mention} `->` {self.bot.head_admin.mention}""")

    # Sets a new admin role
    @commands.command(name="setadmin", aliases=["set_admin"])
    async def _setadmin(self, ctx:commands.Context, role:discord.Role=None) -> None:
        if role is None:
            await self.send(ctx.channel, """You forgot to specify the new admin role
                                            Specify a new role by either pinging the role or by using it's id or name""")
            return

        if role == self.bot.admin:
            await self.send(ctx.channel, f"{role.mention} is already the admin role")
            return

        if role == self.bot.head_admin or role == self.bot.moderator:
            await self.send(ctx.channel, f"""Every staff role has to be unique.
                                    Admin will have access to the commands for moderators but to the commands for head admins""")
            return

        changed_setting = await self.change_settings(ctx, "admin", role.id)
        if changed_setting:
            old_role = self.bot.admin
            self.bot.admin = role
            if old_role is None:
                await self.send(ctx.channel, f"Admin role set to {self.bot.admin.mention}")
            else:
                await self.send(ctx.channel, f"""Admin role changed
                                                {old_role.mention} `->` {self.bot.admin.mention}""")

    # Sets a new moderator role
    @commands.command(name="setmoderator", aliases=["set_moderator"])
    async def _setmoderator(self, ctx:commands.Context, role:discord.Role=None) -> None:
        if role is None:
            await self.send(ctx.channel, """You forgot to specify the new moderator role
                                            Specify a new role by either pinging the role or by using it's id or name""")
            return

        if role == self.bot.head_admin:
            await self.send(ctx.channel, f"{role.mention} is already the moderator role")
            return

        if role == self.bot.head_admin or role == self.bot.admin:
            await self.send(ctx.channel, f"""Every staff role has to be unique.
                                    Moderators will only have access to the commands for moderators""")
            return

        changed_setting = await self.change_settings(ctx, "moderator", role.id)
        if changed_setting:
            old_role = self.bot.moderator
            self.bot.moderator = role
            if old_role is None:
                await self.send(ctx.channel, f"Moderator role set to {self.bot.moderator.mention}")
            else:
                await self.send(ctx.channel, f"""Moderator role changed
                                                {old_role.mention} `->` {self.bot.moderator.mention}""")

    # Sets the embed colour
    @commands.command(name="setembedcolour", aliases=["set_embed_colour", "set_embed_color", "set_embedcolour", "set_embedcolor", "setembedcolor", "set_colour", "set_color", "setcolour", "setcolor"])
    async def _setembedcolour(self, ctx:commands.Context, r:int=None, g:int=None, b:int=None):
        if r is None or g is None or b is None:
            await self.send(ctx.channel, f"""You can change the embed colour by changing it's rgb values.
                                    Seperate each value by a space.
                                    e.g. White would become `{self.bot.prefix}setembedcolour 255 255 255`""")
            return

        if not 0 <= r <= 255 or not 0 <= g <= 255 or not 0 <= b <= 255:
            await self.send(ctx.channel, "A rgb value is between 0 and 255")
            return

        changed_setting = await self.change_settings(ctx, "embed colour", [r, g, b])
        if changed_setting:
            colour = discord.Color.from_rgb(r, g, b)
            self.bot.embed_colour = colour

            await self.send(ctx.channel, "successfully changed the embed colour")


    ###############
    #  Listeners  #
    ###############


    # Triggers when the bot is ready and prints some basic information
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.startup_check()

        print_to_console("\n\tBot started!")
        print("-"*34)
        print(f"Bot name:\t{self.bot.user.name}")
        print(f"Bot ID:\t\t{self.bot.user.id}")
        print(f"Invite link:\thttps://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=10304&scope=bot")
        print("-"*34)
        print(f"Discord server:\t{self.bot.guild.name if self.bot.guild is not None else 'Not set'}")
        print(f"Prefix:\t\t{self.bot.prefix}")
        print(f"Servers:\t{len(self.bot.servers)}")
        print(f"Head admin:\t{self.bot.head_admin.name if self.bot.head_admin is not None else 'Not set'}")
        print(f"Admin:\t\t{self.bot.admin.name if self.bot.admin is not None else 'Not set'}")
        print(f"Moderator:\t{self.bot.moderator.name if self.bot.moderator is not None else 'Not set'}")
        print("-"*34)
        print("\n")
        print_to_console("Bot is running")


# Adds the cog to the bot
def setup(bot:commands.Bot) -> None:
    bot.add_cog(Settings(bot))
