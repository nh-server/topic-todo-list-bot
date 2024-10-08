import os
from traceback import format_exception
import asyncpg
import discord
import sys
from discord.ext import commands
import yaml
import asyncio
from logzero import setup_logger

console_logger = setup_logger(name='mainlogs', logfile='data/logs/main.log', maxBytes=100000)


def read_config(config: str) -> str:
    try:
        with open("data/config.yml", "r") as f:
            loadedYml = yaml.safe_load(f)
            return loadedYml[config]
    except FileNotFoundError:
        print("Cannot find config.yml. Does it exist?")
        sys.exit(1)


async def create_pool():
    return await asyncpg.create_pool(read_config("db"))


class StaffToDoList(commands.Bot):
    """A bot designed to handle incoming messages and anonymously output them to a channel. Then rate them by priority"""

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        super().__init__(command_prefix=read_config('prefix'),
                         description="The bot to handle suggestions from all members of a team!",
                         allow_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False),
                         intents=discord.Intents().all(), help_command=commands.MinimalHelpCommand())

        self.db = self.loop.run_until_complete(create_pool())

    async def prepare_db(self):
        """Sets up database pool for usage"""
        async with self.db.acquire() as conn:
            try:
                with open("schema.sql", 'r') as schema:
                    try:
                        await conn.execute(schema.read())
                    except asyncpg.PostgresError as e:
                        console_logger.exception(
                            "A SQL error has occurred while running the schema, traceback is:\n{}".format("".join(
                                format_exception(type(e), e, e.__traceback__))))
                        print(format_exception(type(e), e, e.__traceback__))
                        sys.exit(-1)

            except FileNotFoundError:
                print(
                    "schema file not found, please check your files, remember to rename schema.sql.example to schema.sql when you would like to use it")
                sys.exit(-1)

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
        await self.prepare_db()
        cog_files = [file[:-3] for file in os.listdir("cogs") if file.endswith(".py")]
        if cog_files:
            for cog in cog_files:
                try:
                    self.load_extension("cogs." + cog)
                    console_logger.info(f"{cog} loaded")

                except Exception as e:
                    console_logger.exception(
                        f"Failed to load {cog}:\n{''.join(format_exception(type(e), e, e.__traceback__))}")

        console_logger.info(f"We are logged in as {self.user.name}!")
        await self.change_presence(
            activity=discord.Activity(name=read_config("activity"), type=discord.ActivityType.listening))


if __name__ == "__main__":
    bot = StaffToDoList()
    try:
        bot.run(read_config("token"))
    except Exception:
        print("Unable to log in")
        sys.exit(1)
