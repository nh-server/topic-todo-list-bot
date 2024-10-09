import discord
from discord import app_commands
from discord.ext import commands


class Settings(commands.Cog):
    """Handles settings"""

    def __init__(self, bot):
        self.bot = bot

    output_channel = app_commands.Group(name="channel", description="Configures the output channel for a guild")

    async def set_guild(self, guild_id: int):
        """Checks if a guild is in the settings database"""
        await self.bot.db.guild_add(guild_id)

    @app_commands.guild_only()
    @output_channel.command(name="set")
    async def channel_set(self, interaction, channel: discord.TextChannel):
        """Sets an output channel"""
        # check if channel exists in db
        if channel not in interaction.guild.channels:
            return await interaction.response.send_message("You cannot set a channel outside this server.", ephemeral=True)

        await self.set_guild(interaction.guild_id)
        await self.bot.db.guild_channel_add(interaction.guild_id, channel.id)
        await interaction.response.send_message(f"Output channel set to: {channel.mention}", ephemeral=True)

    @app_commands.guild_only()
    @output_channel.command(name="unset")
    async def channel_unset(self, interaction):
        """Removes the output channel"""
        await self.set_guild(interaction.guild_id)

        if not await self.bot.db.guild_channel_get(interaction.guild_id):
            return await interaction.response.send_message("No channel set", ephemeral=True)

        else:
            await self.bot.db.guild_channel_remove(interaction.guild_id)
            await interaction.response.send_message("Channel unset", ephemeral=True)

    approved_roles = app_commands.Group(name="roles", description="Configures approved roles for users to submit issues")

    @app_commands.guild_only()
    @approved_roles.command(name="set")
    async def role_set(self, interaction, role: discord.Role):
        """Adds a role to the list"""
        await self.set_guild(interaction.guild_id)
        current_roles = await self.bot.db.guild_role_get(interaction.guild_id)
        if not current_roles or role.id not in current_roles:
            await self.bot.db.guild_role_add(interaction.guild_id, role.id)
            await interaction.response.send_message(f"{role.name} can now submit messages!", ephemeral=True)
        else:
            return await interaction.response.send_message(f"{role.name} is already registered as an approved role!", ephemeral=True)

    @app_commands.guild_only()
    @approved_roles.command(name="unset")
    async def role_unset(self, interaction, role: discord.Role):
        """Adds a role to the list"""
        await self.set_guild(interaction.guild_id)
        current_roles = await self.bot.db.guild_role_get(interaction.guild_id)
        if current_roles or role.id in current_roles:
            await self.bot.db.guild_role_remove(interaction.guild_id, role.id)
            await interaction.response.send_message(f"{role.name} can no longer submit messages.", ephemeral=True)
        else:
            return await interaction.response.send_message(f"{role.name} is not registered.", ephemeral=True)

    @app_commands.guild_only()
    @app_commands.command(name="settings")
    async def settings_list(self, interaction):
        """Gets info for the current server"""
        embed = discord.Embed(title=f"Settings for {interaction.guild.name}", description="Current options set",
                              color=discord.Color.dark_blue())
        data = await self.bot.db.guild_get_all(interaction.guild_id)
        channel = "No channel saved!"
        roles = "None saved!"
        if data:
            if data.get("allowed_role_ids"):
                roles = ""
                for r in data['allowed_role_ids']:
                    role = interaction.guild.get_role(r)
                    roles += f"- {role} ({role.id})\n"

            if data.get('output_channel_id'):
                channel = data['output_channel_id']

        embed.add_field(name="Output Channel", value=channel)
        embed.add_field(name="Approved roles", value=roles)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Settings(bot))
