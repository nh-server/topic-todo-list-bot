import discord
from discord.ext import commands, flags
from utils.menu import YesNoMenu


class Message(commands.Cog):
    """Handles incoming dms and outputting"""

    def __init__(self, bot):
        self.bot = bot

    async def react_check(self, payload):
        """Checks reaction for a thumbs up"""
        if payload.member and payload.member.id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        output_channel_id = await self.bot.db.fetchval("SELECT output_channel_id FROM settings WHERE guild_id = $1",
                                                       guild.id)
        channel = guild.get_channel(output_channel_id)
        if payload.channel_id != output_channel_id:
            return

        if payload.emoji.name == "👍":
            message = await channel.get_partial_message(payload.message_id).fetch()
            plus_one = [r for r in message.reactions if r.emoji == "👍"][0]
            await self.bot.db.execute("UPDATE todo SET priority_level = $1 WHERE message_id = $2", plus_one.count,
                                      payload.message_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Update priority count"""
        await self.react_check(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Update priority count"""
        await self.react_check(payload)

    @commands.dm_only()
    @commands.command()
    async def send(self, ctx, guild_id: int, *, msg):
        """Send a message"""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return await ctx.send("Invalid server ID given")
        member = guild.get_member(ctx.author.id)
        data = await self.bot.db.fetchrow(
            "SELECT output_channel_id, allowed_role_ids FROM settings WHERE guild_id = $1", guild.id)
        if not data:
            return await ctx.send(f"Bot is not configured for {guild.name}. Please contact and admin!")

        has_role = None
        if data['allowed_role_ids']:
            guild_role_set = set(member.roles)
            db_roles = set([guild.get_role(x) for x in data['allowed_role_ids']])
            res = (db_roles & guild_role_set)
            if res:
                has_role = res.pop()

        if not has_role:
            return await ctx.send(f"You cannot submit topics to {guild.name}")

        if not data['output_channel_id'] or not guild.get_channel(data['output_channel_id']):
            return await ctx.send(f"Bot is not configured for {guild.name}. Please contact and admin!")

        channel = guild.get_channel(data['output_channel_id'])
        if not channel:
            return await ctx.send("Cannot output to channel, cannot find id")
        embed = discord.Embed(title="Topic posted", color=discord.Color.gold())
        embed.description = msg
        res, confirm_msg = await YesNoMenu(
            f"Are you sure you want to send this message to {guild.name}? Below is a preview", embed=embed).prompt(ctx)
        if not res:
            return await confirm_msg.edit(content="Cancelled")
        posted_message = await channel.send(embed=embed)
        await posted_message.add_reaction("\U0001f44d")
        await self.bot.db.execute(
            "INSERT INTO todo (guild_id, message, priority_level, message_id, message_link) VALUES ($1, $2, $3, $4, $5)",
            guild.id, msg,
            1, posted_message.id, f"https://discord.com/channels/{guild.id}/{channel.id}/{posted_message.id}")
        await confirm_msg.edit(content=f"Topic submitted to {guild.name}")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command()
    async def close(self, ctx, message: discord.Message, outcome: str, *, reason: str):
        """
        Closes an topic requires administrator perms
        """
        if not outcome.lower() in ('accept', 'deny'):
            return await ctx.send("Please specify if you are accepting or denying this suggestion")

        db_msg_id = await self.bot.db.fetchval("SELECT id FROM todo WHERE message_id = $1", message.id)

        embed = message.embeds[0]
        desc = "~~" + embed.description + "~~"
        embed.description = desc
        embed.add_field(name="Resolved",
                        value=f"This topic has been resolved by administrators for the following reason:\n```{reason}```")
        if outcome.lower() == "accept":
            embed.color = discord.Color.green()
        else:
            embed.color = discord.Color.red()

        await message.edit(embed=embed)
        await self.bot.db.execute("DELETE FROM todo WHERE id = $1", db_msg_id)
        await ctx.send(f"Closed topic id {db_msg_id}")

    @commands.guild_only()
    @commands.command(name="listopen")
    async def list_open(self, ctx):
        """List current issues that are on the table (Only can be ran by the approved role)"""
        approved_roles = await self.bot.db.fetchval("SELECT allowed_role_ids FROM settings WHERE guild_id = $1",
                                                    ctx.guild.id)
        if approved_roles:
            approved_roles = set(approved_roles)
        else:
            return await ctx.send("You cannot use this.")
        has_role = (approved_roles & set([r.id for r in ctx.author.roles]))
        if not has_role:
            return await ctx.send("You cannot use this.")

        active_todo_list = await self.bot.db.fetch(
            "SELECT id, message, priority_level, message_link FROM todo WHERE guild_id = $1 ORDER BY priority_level DESC",
            ctx.guild.id)
        embed = discord.Embed(title=f"On going issues and suggestions for {ctx.guild.name}",
                              color=discord.Color.orange())
        if active_todo_list:
            for todo in active_todo_list:
                if len(todo['message']) > 20:
                    trucated_message = todo['message'][0:20] + "..."
                else:
                    trucated_message = todo['message']
                if todo['priority_level'] >= 10:
                    embed.add_field(name=f"**ID: {todo['id']} Priority Level: {todo['priority_level']}**",
                                    value="**" + trucated_message + f"**\nLink to post: {todo['message_link']}",
                                    inline=False)
                else:
                    embed.add_field(name=f"ID: {todo['id']} Priority Level: {todo['priority_level']}",
                                    value=f"{trucated_message}\nLink to post: {todo['message_link']}", inline=False)
        elif len(embed.fields) == 0:
            embed.description = "No open topics!"

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Message(bot))
