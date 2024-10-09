import os
from traceback import format_exception
import asyncpg
import discord
import sys
from discord.ext import commands
import yaml
import asyncio
import logging

from utils.sql import SQLDB


console_logger = logging.getLogger("main")


def read_config(config: str) -> str:
    try:
        with open("data/config.yml", "r") as f:
            loadedYml = yaml.safe_load(f)
            return loadedYml[config]
    except FileNotFoundError:
        print("Cannot find config.yml. Does it exist?")
        sys.exit(1)


class StaffToDoList(commands.Bot):
    """A bot designed to handle incoming messages and anonymously output them to a channel. Then rate them by priority"""

    def __init__(self):
        super().__init__(command_prefix=read_config('prefix'),
                         description="The bot to handle suggestions from all members of a team!",
                         allow_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False),
                         intents=discord.Intents().all(), help_command=commands.MinimalHelpCommand())
        self.db = SQLDB(self)

    async def setup_hook(self) -> None:
        await self.db.startup()
        await self.load_cogs()
        await self.tree.sync()

    async def load_cogs(self):
        cog_files = [file[:-3] for file in os.listdir("cogs") if file.endswith(".py")]
        if cog_files:
            for cog in cog_files:
                try:
                    await self.load_extension("cogs." + cog)
                    console_logger.info(f"{cog} loaded")

                except Exception as e:
                    console_logger.exception(
                        f"Failed to load {cog}:\n{''.join(format_exception(type(e), e, e.__traceback__))}")

    async def on_command_error(self, ctx, error):
        """Handles errors"""
        # handles errors for commands that do not exist
        if isinstance(error, commands.errors.CommandNotFound):
            return

        # handles all uncaught http connection failures.
        elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.HTTPException):
            await ctx.send(
                f"An HTTP {error.original.status} error has occurred for the following reason: `{error.original.text}`")

        # handles all bad command usage
        elif isinstance(error, (
                commands.MissingRequiredArgument, commands.BadArgument, commands.BadUnionArgument,
                commands.TooManyArguments)):
            await ctx.send_help(ctx.command)

        # handles commands that are attempted to be used outside a guild.
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.send("You cannot use this command outside of a server!")

        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("You cannot use this command outside of DMs with the bot!")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(error.args[0])

        else:
            await ctx.send(f"An error occurred while processing the `{ctx.command.name}` command.")
            print('Ignoring exception in command {0.command} in {0.message.channel}'.format(ctx))
            try:
                log_msg = "Exception occurred in `{0.command}` in {0.message.channel.mention}".format(ctx)
                console_logger.info(f"COMMAND: {ctx.command.name}, GUILD: {ctx.guild.name} CHANNEL: {ctx.channel.name}")
            except Exception:
                log_msg = "Exception occurred in `{0.command}` in DMs with a user".format(ctx)
            tb = format_exception(type(error), error, error.__traceback__)
            print(''.join(tb))
            console_logger.exception(log_msg + "".join(tb) + '\n\n')

    async def on_ready(self):
        """Loads code on boot"""
        console_logger.info(f"We are logged in as {self.user.name}!")
        await self.change_presence(
            activity=discord.Activity(name=read_config("activity"), type=discord.ActivityType.listening))


async def startup():
    discord.utils.setup_logging(handler=logging.FileHandler('/data/main.log', encoding='utf-8', mode='w'))
    # stream handler
    discord.utils.setup_logging()

    bot = StaffToDoList()
    await bot.start(read_config("token"))


if __name__ == "__main__":
    asyncio.run(startup())
