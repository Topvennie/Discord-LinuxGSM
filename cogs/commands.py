import asyncio
import os
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
from server import Server
from utils import get_unix_time, send


# Class for all the server commands
class Commands(commands.Cog):

    def __init__(self, bot:commands.Bot) -> None:
        self.bot = bot
        self.servers = self.make_servers_variable()
        self.messages = {}
        self.emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

    # Makes the self.servers variable
    def make_servers_variable(self) -> dict:
        servers = {}
        for server in self.bot.servers:
            servers[server.name] = server

        return servers


    ############
    #  Checks  #
    ############


    # Cog check 
    def cog_check(self, ctx:commands.Context) -> bool:        
        return self.bot.head_admin in ctx.author.roles or self.bot.admin in ctx.author.roles or self.moderator in ctx.author.roles or ctx.author.guild_permissions.administrator


    ###############
    #  Cog Utils  #
    ###############


    # Generic function to write content to a file
    def write_to_file(self, location:str, content:str) -> bool:
        try:
            with open(location, "w") as file:
                file.write(content)
        except:
            return False

        return True

    # Generic function to delete a file
    def delete_file(self, file_location:str) -> bool:
        if os.path.exists(file_location):
            try:
                os.remove(file_location)
                return True
            except:
                return False
        return False

    # Removes a message from self.messages
    def remove_message(self, message:discord.Message) -> bool:
        try:
            del self.messages[message]
        except KeyError:
            return False

        return True

    # Generic function to send code blocks
    async def send_message(self, channel:discord.TextChannel, content:str, delete_after:int=None) -> Optional[discord.Message]:
        try:
            msg = await channel.send(content, delete_after=delete_after)
        except discord.errors.Forbidden:
            info = await self.bot.application_info()
            owner = info.owner
            try:
                await owner.send(f"""I am unable to send messages in {channel.name}.
                                    Without the proper permissions I'm unable to function properly!""")
            except discord.errors.Forbidden:
                pass
            return None

        return msg

    # Generic function to send files
    async def send_file(self, channel:discord.TextChannel, file_location:str, filename:str=None, delete_after:int=None) -> Optional[discord.Message]:
        try:
            msg = await channel.send(file=discord.File(file_location, filename=filename if filename is not None else ""), delete_after=delete_after)
        except discord.errors.Forbidden:
            info = await self.bot.application_info()
            owner = info.owner
            try:
                await owner.send(f"""I am unable to send messages in {channel.name}.
                                    Without the proper permissions I'm unable to function properly!""")
            except discord.errors.Forbidden:
                pass
            return None
        
        return msg

    # Checks if everything is in order
    async def process_command(self, message:discord.Message, server:Server) -> None:
        # Limits to one concurrent menu / server
        for msg in self.messages:
            if msg.embeds[0].title == message.content:
                await send(self.bot, msg.channel, description=f"""There already is a menu open to execute a command for that server!
                                                            {msg.jump_url}""")
                return

        if self.bot.head_admin in message.author.roles or message.author.guild_permissions.administrator:
            commands = server.head_admin
        elif self.bot.admin in message.author.roles:
            commands = server.admin
        else:
            commands = server.moderator

        # Checks if the bot has the right permissions
        perms = message.channel.permissions_for(message.guild.me)
        if not perms.send_messages or not perms.manage_messages:
            await send(self.bot, message.channel, description=f"""I don't have the right permissions in {message.channel.mention}
                                                            I require the `manage messages` and `send messages` permissions to function properly""")
            return

        if commands == []:
            return

        description = ""
        for i in range(0, len(commands)):
            description += f"`{i + 1}.` {commands[i].name}\n"

        msg = await send(self.bot, message.channel, description, title=message.content)
        for i in range(0, len(commands)):
            await msg.add_reaction(self.emoji[i])

        reaction_deleter = ReactionDeleter(self, msg, 30)
        self.messages[msg] = [reaction_deleter, commands]

    # handles reactions being added if it's to go to a different page
    # TODO
    async def handle_pages(self) -> None:
        pass

    # Handles reactions being added
    async def handle_reactions(self, reaction:discord.Reaction, member:discord.Member) -> None:
        # Get reaction index
        try:
            index = self.emoji.index(reaction.emoji)
        except ValueError:
            return

        # Get command and the server object
        try:
            command = self.messages[reaction.message][1][index]
            server_object = self.servers[reaction.message.embeds[0].title]
        except KeyError:
            return

        # Checks if the member has access to the command
        if not self.bot.head_admin in member.roles or not member.guild_permissions.administrator:
            if command in server_object.admin and self.bot.admin not in member.roles:
                if self.bot.moderator not in member.roles:
                    return
        
        # Construct embed
        self.messages[reaction.message][0].delete_now()
        description = f"""{member.mention} used `{command}`\n\n
                        Executing the command..."""
        starttime = datetime.now()
        embed = discord.Embed(
            title=server_object.name,
            description=description,
            colour=self.bot.embed_colour
        )
        embed.set_footer(text=f"Start: {starttime.strftime('%H:%M:%S')}")

        await reaction.message.edit(embed=embed)

        result = await server_object.execute(command, self.bot, reaction.message.channel, member)

        if result[0]:
            description = f"""{member.mention} used `{command}`\n
                        ✅ Succesfully executed the command"""
        elif result[3]:
            description = f"""{member.mention} used `{command}`\n
                        ❌ Failed to execute the command
                        {command} requires input"""
        elif not result[0] and result[1] is None and result[2] is None:
            description = f"""{member.mention} used `{command}`\n
                        ❌ Could not find the command
                        Please try refreshing your serverlist with `{self.bot.prefix}refresh`"""
        else:
            description = f"""{member.mention} used `{command}`\n
                        ❌ Failed to execute the command"""

        embed.description = description
        endtime = datetime.now()
        duration = endtime - starttime

        # Don't show the duration if it takes less than 5 seconds
        if duration.seconds >= 5:
            embed.set_footer(text=f"Start: {starttime.strftime('%H:%M:%S')} ▫️ End: {endtime.strftime('%H:%M:%S')} ▫️ Duration: {str(duration).split('.')[0]}")
        else:
            embed.set_footer(text=f"Start: {starttime.strftime('%H:%M:%S')} ▫️ End: {endtime.strftime('%H:%M:%S')}")

        await reaction.message.edit(embed=embed)

        if result[1] is not None:
            if len(result[1]) < 3800:
                await self.send_message(reaction.message.channel, f"Output:\n```bash\n{result[1]}```", delete_after=300)
            else:
                file_location = f"./tmp/{str(reaction.message.id)}"
                file = self.write_to_file(file_location, result[2])
                if file:
                    await self.send_file(reaction.message.channel, file_location, "Output", delete_after=300)
                    self.delete_file(file_location)
        if result[2] is not None:
            if len(result[2]) < 3800:
                await self.send_message(reaction.message.channel, f"Errors:\n```bash\n{result[2]}```", delete_after=300)
            else:
                file_location = f"./tmp/{str(reaction.message.id)}"
                file = self.write_to_file(f"./tmp/{str(reaction.message.id)}", result[2])
                if file:
                    await self.send_file(reaction.message.channel, file_location, "Errors", delete_after=300)
                    self.delete_file(file_location)


    ##############
    #  Commands  #
    ##############


    # Command to give an overview of all the available servers for their role
    @commands.command(name="servers")
    async def _servers(self, ctx:commands.Context) -> None:
        head_admin = False
        admin = False
        moderator = False

        # Check the role of the user
        if self.bot.head_admin in ctx.author.roles or ctx.author.guild_permissions.administrator:
            head_admin = True
        elif self.bot.admin in ctx.author.roles:
            admin = True
        else:
            moderator = True

        description=""
        i = 1

        # Adds server to description if the user has access to any of it's commands
        for server in self.bot.servers:
            if head_admin and server.head_admin != []:
                description += f"`{i}.` {server.name}\n"
            elif admin and server.admin != []:
                description += f"`{i}.` {server.name}\n"
            elif moderator and server.moderator != []:
                description += f"`{i}.` {server.name}\n"
            i += 1

        if description == "" and len(self.bot.servers) == 0:
            if len(self.bot.servers) == 0:
                await send(self.bot, ctx.channel, description="There aren't any servers set up yet")
            else:
                await send(self.bot, ctx.channel, description="You don't have access to any of the current servers")
        else:
            await send(self.bot, ctx.channel, description=description)


    ###############
    #  Listeners  #
    ###############


    # Listens to a command for any of the servers
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message) -> None:
        if message.guild != self.bot.guild:
            return

        if message.author.bot:
            return

        if not message.content.startswith(self.bot.prefix):
            return

        if message.content.replace(self.bot.prefix, "") in self.servers.keys():
            message.content = message.content.replace(self.bot.prefix, "")
            await self.process_command(message, self.servers[message.content])
        else :
            await self.bot.process_commands(message)

    # Deletes the message data if the message gets deleted
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message in self.messages.keys():
            try:
                del self.messages[message]
            except KeyError:
                return

    # If an user deletes a reaction the reactions get removed
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if reaction.message not in self.messages.keys():
            return
        
        if user.bot:
            return
        
        reaction_deleter = self.messages[reaction.message][0]
        reaction_deleter.delete_now()

    # If an user adds a reaction
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message not in self.messages.keys():
            return
        
        if user.bot:
            return

        if reaction.emoji in self.pages:
            await self.handle_pages()
        else:
            await self.handle_reactions(reaction, user)


# Class to keep track on when to delete the reactions
class ReactionDeleter():
    def __init__(self, commands_object:Commands, message:discord.Message, timeout:int) -> None:
        self.commands_object = commands_object
        self.message = message
        self.timeout = timeout
        self.delete_time = get_unix_time() + self.timeout
        asyncio.create_task(self.timer())

    # Sets a new timer for when the reaction need to be deleted. Handy if you want to overwrite the current timer
    def next_delete(self, timeout:int) -> None:
        self.delete_time = get_unix_time() + timeout
        asyncio.create_task(self.timer())

    # Immediately starts the task to delete all reactions
    def delete_now(self) -> None:
        asyncio.create_task(self.remove_reactions())

    # Starts the task to delete the reactions if the timer hasn't been overwritten
    async def timer(self) -> None:
        await asyncio.sleep(self.timeout)

        if get_unix_time() <= self.delete_time:
            await self.remove_reactions()

    # Removes all reactions
    async def remove_reactions(self) -> None:
        try:
            await self.message.clear_reactions()
        except (discord.errors.Forbidden, discord.errors.NotFound):
            return

        self.commands_object.remove_message(self.message)


# Adds the cog to the bot
def setup(bot:commands.Bot) -> None:
    bot.add_cog(Commands(bot))
