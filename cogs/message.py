import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from utils.menu import YesNoView


class Message(commands.Cog):
    """Handles incoming dms and outputting"""

    def __init__(self, bot):
        self.bot = bot

    def construct_message_link(self, guild_id: int, channel_id: int, message_id: int):
        return f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

    async def react_check(self, payload):
        """Checks reaction for a thumbs up"""
        if payload.member and payload.member.id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        output_channel_id = await self.bot.db.guild_channel_get(guild.id)
        channel = guild.get_channel(output_channel_id)
        if payload.channel_id != output_channel_id:
            return

        if payload.emoji.name == "👍":
            message = await channel.get_partial_message(payload.message_id).fetch()
            plus_one = [r for r in message.reactions if r.emoji == "👍"][0]
            await self.bot.db.message_update(payload.message_id, plus_one.count)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Update priority count"""
        await self.react_check(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Update priority count"""
        await self.react_check(payload)

    @app_commands.guild_only()
    @app_commands.command()
    async def send(self, interaction: discord.Interaction, title: str, message: str):
        """Send a message"""
        # Sanity check input
        # The actual max is 256, but we'll just reserve a bit.
        # In most cases nobody is actually writing 200 char long titles
        if len(title) > 200:
            return await interaction.response.send_message(f"Title is too long! Limit is 200 characters, input is {len(title)}.", ephemeral=True)
        # The actual max is 4096, but we'll just reserve a bit.
        # Hopefully nobody writes an entire essay...
        if len(message) > 4000:
            return await interaction.response.send_message(f"Message is too long! Limit is 4000 characters, input is {len(message)}.", ephemeral=True)

        guild = interaction.guild
        data = await self.bot.db.guild_get_all(guild.id)
        if not data:
            return await interaction.response.send_message(f"Bot is not configured for {guild.name}. Please contact and admin!", ephemeral=True)

        if not data['output_channel_id'] or not guild.get_channel(data['output_channel_id']):
            return await interaction.response.send_message(f"Bot is not configured for {guild.name}. Please contact and admin!", ephemeral=True)

        channel = guild.get_channel(data['output_channel_id'])
        if not channel:
            return await interaction.response.send_message("Cannot output to channel, cannot find id", ephemeral=True)
        embed = discord.Embed(title=f"Topic: {title}", color=discord.Color.gold())
        embed.description = message
        view = YesNoView(interaction)
        await interaction.response.send_message(f"Are you sure you want to send this message to {guild.name}? Below is a preview", embed=embed, view=view, ephemeral=True)
        await view.wait()
        if not view.result:
            return await interaction.edit_original_response(content="Cancelled", view=None)
        posted_message = await channel.send(embed=embed)
        await posted_message.add_reaction("\U0001f44d")
        await self.bot.db.message_add(guild.id, title, message, posted_message.id)
        db_msg = await self.bot.db.message_get_by_message(posted_message.id)
        embed.title = f"Topic #{db_msg['id']}: {title}"
        await posted_message.edit(embed=embed)
        await interaction.edit_original_response(content=f"Topic submitted to {guild.name}", view=None)

    @app_commands.guild_only()
    @app_commands.choices(
        outcome=[
            Choice(name='Accepted', value='accept',),
            Choice(name='Denied', value='deny'),
        ]
    )
    @app_commands.command()
    async def close(self,
                    interaction: discord.Interaction,
                    topic: int,
                    outcome: str,
                    reason: str):
        """
        Closes an topic requires administrator perms

        Args:
            topic: The topic number
            outcome: Decision made by administrators (Accepted, Denied)
            reason: The reason behind the outcome
        """
        guild = interaction.guild
        data = await self.bot.db.guild_get_all(guild.id)
        if not data:
            return await interaction.response.send_message(f"Bot is not configured for {guild.name}. Please contact and admin!", ephemeral=True)

        if not data['output_channel_id'] or not guild.get_channel(data['output_channel_id']):
            return await interaction.response.send_message(f"Bot is not configured for {guild.name}. Please contact and admin!", ephemeral=True)

        if not outcome.lower() in ('accept', 'deny'):
            return await interaction.response.send_message("Please specify if you are accepting or denying this suggestion", ephemeral=True)

        db_msg = await self.bot.db.message_get_by_id(topic)
        channel = guild.get_channel(data['output_channel_id'])
        message = await channel.fetch_message(db_msg['message_id'])

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
        await self.bot.db.message_remove(db_msg['id'])
        await interaction.response.send_message(f"Closed topic id {db_msg['id']}", ephemeral=True)

    @app_commands.guild_only()
    @app_commands.command(name="listopen")
    async def list_open(self, interaction: discord.Interaction):
        """List current issues that are on the table"""
        active_todo_list = await self.bot.db.message_get_all(interaction.guild_id)
        guild_channel = await self.bot.db.guild_channel_get(interaction.guild.id)
        embed = discord.Embed(title=f"On going issues and suggestions for {interaction.guild.name}",
                              color=discord.Color.orange())
        if active_todo_list:
            for todo in active_todo_list:
                if len(todo['title']) > 20:
                    trucated_message = todo['title'][0:20] + "..."
                else:
                    trucated_message = todo['title']
                if todo['priority_level'] >= 10:
                    embed.add_field(name=f"**ID: {todo['id']} Priority Level: {todo['priority_level']}**",
                                    value=f"**Title: {trucated_message}**\nLink to post: {self.construct_message_link(interaction.guild.id, guild_channel, todo['message_id'])}",
                                    inline=False)
                else:
                    embed.add_field(name=f"ID: {todo['id']} Priority Level: {todo['priority_level']}",
                                    value=f"Title: {trucated_message}\nLink to post: {self.construct_message_link(interaction.guild.id, guild_channel, todo['message_id'])}", inline=False)
        elif len(embed.fields) == 0:
            embed.description = "No open topics!"

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Message(bot))
