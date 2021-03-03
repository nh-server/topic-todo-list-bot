import discord
from discord.ext import commands


class Settings(commands.Cog):
    """Handles settings"""

    def __init__(self, bot):
        self.bot = bot

    async def set_guild(self, guild_id: int):
        """Checks if a guild is in the settings database"""
        if not await self.bot.db.fetchval("SELECT guild_id FROM settings WHERE guild_id = $1", guild_id):
            await self.bot.db.execute("INSERT INTO settings (guild_id) VALUES ($1)", guild_id)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(name="channel", invoke_without_command=True)
    async def output_channel(self, ctx):
        """Manages the output channel, can only be set by someone with admin perms"""
        await ctx.send_help(ctx.command)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @output_channel.command(name="set")
    async def channel_set(self, ctx, channel: discord.TextChannel):
        """Sets an output channel"""
        # check if channel exists in db
        if channel not in ctx.guild.channels:
            return await ctx.send("You cannot set a channel outside this server.")

        await self.set_guild(ctx.guild.id)
        await self.bot.db.execute("UPDATE settings SET output_channel_id = $1 WHERE guild_id = $2", channel.id,
                                  ctx.guild.id)
        await ctx.send(f"Output channel set to: {channel.mention}")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @output_channel.command(name="unset")
    async def channel_unset(self, ctx):
        """Removes the output channel"""
        await self.set_guild(ctx.guild.id)

        if not await self.bot.db.fetchval("SELECT output_channel_id FROM settings WHERE guild_id = $1", ctx.guild.id):
            return await ctx.send("No channel set")

        else:
            await self.bot.db.execute("UPDATE settings SET output_channel_id = NULL WHERE guild_id = $1", ctx.guild.id)
            await ctx.send("Channel unset")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.group(name="roles", invoke_without_command=True)
    async def approved_roles(self, ctx):
        """Sets approved roles for users to submit issues"""
        await ctx.send_help(ctx.command)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @approved_roles.command(name="set")
    async def role_set(self, ctx, role: discord.Role):
        """Adds a role to the list"""
        await self.set_guild(ctx.guild.id)
        current_roles = await self.bot.db.fetchval("SELECT allowed_role_ids FROM settings WHERE guild_id = $1",
                                                   ctx.guild.id)
        if not current_roles or not role.id in current_roles:
            await self.bot.db.execute(
                "UPDATE settings SET allowed_role_ids = array_append(allowed_role_ids, $1::BIGINT) WHERE guild_id = $2",
                role.id, ctx.guild.id)
            await ctx.send(f"{role.name} can now submit messages!")
        else:
            return await ctx.send(f"{role.name} is already registered as an approved role!")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @approved_roles.command(name="unset")
    async def role_unset(self, ctx, role: discord.Role):
        """Adds a role to the list"""
        await self.set_guild(ctx.guild.id)
        current_roles = await self.bot.db.fetchval("SELECT allowed_role_ids FROM settings WHERE guild_id = $1",
                                                   ctx.guild.id)
        if current_roles or role.id in current_roles:
            await self.bot.db.execute(
                "UPDATE settings SET allowed_role_ids = array_remove(allowed_role_ids, $1) WHERE guild_id = $2",
                role.id, ctx.guild.id)
            await ctx.send(f"{role.name} can no longer  submit messages.")
        else:
            return await ctx.send(f"{role.name} is not registered.")

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="info", aliases=['settings'])
    async def settings_list(self, ctx):
        """Gets info for the current server"""
        embed = discord.Embed(title=f"Settings for {ctx.guild.name}", description="Current options set",
                              color=discord.Color.dark_blue())
        data = await self.bot.db.fetchrow(
            "SELECT output_channel_id, allowed_role_ids FROM settings WHERE guild_id = $1", ctx.guild.id)
        channel = "No channel saved!"
        roles = "None saved!"
        if data:
            if data.get("allowed_role_ids"):
                roles = ""
                for r in data['allowed_role_ids']:
                    role = ctx.guild.get_role(r)
                    roles += f"- {role} ({role.id})\n"

            if data.get('output_channel_id'):
                channel = data['output_channel_id']

        embed.add_field(name="Output Channel", value=channel)
        embed.add_field(name="Approved roles", value=roles)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Settings(bot))
