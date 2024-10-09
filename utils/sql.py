#
# Copyright (C) 2021-2024 lifehackerhansol
#
# SPDX-License-Identifier: MIT
#


import logging
import sys
from traceback import format_exception

import asyncpg
import yaml


console_logger = logging.getLogger("main")


class SQLDB():
    def __init__(self, bot):
        self.bot = bot

    def read_config(self, config: str) -> str:
        try:
            with open("data/config.yml", "r") as f:
                loadedYml = yaml.safe_load(f)
                return loadedYml[config]
        except FileNotFoundError:
            print("Cannot find config.yml. Does it exist?")
            sys.exit(1)

    async def startup(self):
        """Sets up database pool for usage"""
        self.db = await asyncpg.create_pool(self.read_config("db"))

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

    async def message_update(self, message_id, count):
        await self.db.execute("UPDATE todo SET priority_level = $1 WHERE message_id = $2", count,
                                    message_id)

    async def message_add(self, guild_id, message, priority_level, message_id, message_link):
        await self.db.execute(
            "INSERT INTO todo (guild_id, message, priority_level, message_id, message_link) VALUES ($1, $2, $3, $4, $5)",
            guild_id, message,
            1, message_id, message_link)

    async def message_get_all(self, guild_id):
        return await self.db.fetch(
            "SELECT id, message, priority_level, message_link FROM todo WHERE guild_id = $1 ORDER BY priority_level DESC",
            guild_id)

    async def message_get(self, message_id):
        return await self.db.fetchval("SELECT id FROM todo WHERE message_id = $1", message_id)

    async def message_remove(self, message_id):
        await self.db.execute("DELETE FROM todo WHERE id = $1", message_id)

    async def guild_add(self, guild_id: int):
        """Checks if a guild is in the settings database"""
        if not await self.db.fetchval("SELECT guild_id FROM settings WHERE guild_id = $1", guild_id):
            await self.db.execute("INSERT INTO settings (guild_id) VALUES ($1)", guild_id)

    async def guild_get_all(self, guild_id):
        return await self.db.fetchrow(
            "SELECT output_channel_id, allowed_role_ids FROM settings WHERE guild_id = $1", guild_id)

    async def guild_channel_add(self, guild_id, channel_id):
        await self.db.execute("UPDATE settings SET output_channel_id = $1 WHERE guild_id = $2", channel_id,
                                  guild_id)

    async def guild_channel_get(self, guild_id):
        return await self.db.fetchval("SELECT output_channel_id FROM settings WHERE guild_id = $1", guild_id)

    async def guild_channel_remove(self, guild_id):
        await self.db.execute("UPDATE settings SET output_channel_id = NULL WHERE guild_id = $1", guild_id)

    async def guild_role_get(self, guild_id):
        return await self.db.fetchval("SELECT allowed_role_ids FROM settings WHERE guild_id = $1",
                                                   guild_id)

    async def guild_role_add(self, guild_id, role_id):
        await self.db.execute("UPDATE settings SET allowed_role_ids = array_append(allowed_role_ids, $1::BIGINT) WHERE guild_id = $2",
                role_id, guild_id)

    async def guild_role_remove(self, guild_id, role_id):
        await self.db.execute(
                "UPDATE settings SET allowed_role_ids = array_remove(allowed_role_ids, $1) WHERE guild_id = $2",
                role_id, guild_id)
