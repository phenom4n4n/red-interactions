from __future__ import annotations

import asyncio
import logging
from enum import IntEnum
from typing import List, Union

import discord
from redbot.core.bot import Red

log = logging.getLogger("red.interactions.models.interactions")

__all__ = (
    "InteractionCallbackType",
    "InteractionMessage",
    "InteractionResponse",
)


class InteractionCallbackType(IntEnum):
    pong = 1
    channel_message_with_source = 4
    deferred_channel_message_with_source = 5
    deferred_update_message = 6
    update_message = 7


class InteractionMessage(discord.Message):
    def __init__(
        self,
        interaction: InteractionResponse,
        *,
        state: discord.state.AutoShardedConnectionState,
        channel: discord.TextChannel,
        data: dict,
    ):
        super().__init__(state=state, channel=channel, data=data)
        self.interaction = interaction
        self.http = interaction.http
        self._token = interaction._token

    async def edit(
        self,
        *,
        content: str = None,
        embed: discord.Embed = None,
        embeds: List[discord.Embed] = None,
        allowed_mentions: discord.AllowedMentions = None,
    ):
        return await self.http.edit_message(
            self._token,
            self.id,
            content=content,
            embed=embed,
            embeds=embeds,
            allowed_mentions=allowed_mentions,
        )

    async def delete(self, *, delay=None):
        if delay is not None:

            async def delete():
                await asyncio.sleep(delay)
                try:
                    await self.http.delete_message(self._token, self.id)
                except discord.HTTPException:
                    pass

            asyncio.create_task(delete())
        else:
            await self.http.delete_message(self._token, self.id)

    @property
    def reply(self):
        return self.interaction.send


class InteractionResponse:
    __slots__ = (
        "state",
        "bot",
        "http",
        "_discord_state",
        "id",
        "version",
        "_token",
        "_original_data",
        "guild_id",
        "channel_id",
        "_channel",
        "application_id",
        "author_id",
        "author",
        "interaction_data",
        "sent",
        "deferred",
        "completed",
    )

    def __init__(self, *, state: "InteractionState", data: dict):
        self.state = state
        self.bot = state.bot
        self.http = state.http
        self._discord_state: discord.state.AutoShardedConnectionState = self.bot._connection
        self.id = int(data["id"])
        self.version = data["version"]
        self._token = data["token"]
        self._original_data = data

        self.guild_id = guild_id = discord.utils._get_as_snowflake(data, "guild_id")
        self.channel_id = discord.utils._get_as_snowflake(data, "channel_id")
        self._channel = None
        self.application_id = discord.utils._get_as_snowflake(data, "application_id")

        if guild_id:
            member_data = data["member"]
            self.author_id = int(member_data["user"]["id"])
            self.author = discord.Member(
                data=member_data, state=self._discord_state, guild=self.guild
            )
        else:
            member_data = data["user"]
            self.author_id = int(member_data["id"])
            self.author = discord.User(data=member_data, state=self._discord_state)

        self.interaction_data = data["data"]
        self.sent = False
        self.deferred = False
        self.completed = False

    def __repr__(self):
        return (
            f"<{type(self).__name__} id={self.id} channel={self.channel!r} author={self.author!r}>"
        )

    @property
    def guild(self) -> discord.Guild:
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self) -> discord.TextChannel:
        if channel := self._channel:
            return channel
        elif self.guild_id:
            if guild_channel := self.guild.get_channel(self.channel_id):
                self._channel = channel
                return guild_channel
        elif dm_channel := self.bot.get_channel(self.channel_id):
            self._channel = dm_channel
            return dm_channel

    async def get_channel(self) -> Union[discord.TextChannel, discord.DMChannel]:
        if channel := self.channel:
            return channel
        if not self.guild_id:
            self._channel = await self.author.create_dm()
        else:
            self._channel = await self.bot.fetch_channel(self.channel_id)
        return self._channel

    @property
    def created_at(self):
        return discord.utils.snowflake_time(self.id)

    async def send(
        self,
        content: str = None,
        *,
        embed: discord.Embed = None,
        embeds: List[discord.Embed] = [],
        tts: bool = False,
        allowed_mentions: discord.AllowedMentions = None,
        hidden: bool = False,
        delete_after: int = None,
        reference=None,  # this parameter and the one below are unused
        mention_author=None,  # they exist to prevent replies from erroring
    ):
        flags = 64 if hidden else None
        initial = not self.sent
        data = await self.http.send_message(
            self._token,
            self.id,
            type=InteractionCallbackType.channel_message_with_source,
            initial_response=initial,
            content=content,
            embed=embed,
            embeds=embeds,
            allowed_mentions=allowed_mentions,
            tts=tts,
            flags=flags,
        )

        if initial:
            self.sent = True
        if not self.completed:
            self.completed = True

        if data:
            try:
                message = InteractionMessage(
                    self,
                    data=data,
                    channel=self.channel,
                    state=self._discord_state,
                )
            except Exception as e:
                log.exception("Failed to create message object for data:\n%r", data, exc_info=e)
            else:
                if delete_after is not None:
                    await message.delete(delay=delete_after)
                return message

    reply = send

    async def defer(self, *, hidden: bool = False):
        flags = 64 if hidden else None
        initial = not self.sent
        data = await self.http.send_message(
            self._token,
            self.id,
            type=InteractionCallbackType.deferred_channel_message_with_source,
            initial_response=initial,
            flags=flags,
        )
        if not self.sent:
            self.sent = True
        self.deferred = True
        return data
