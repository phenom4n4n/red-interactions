import logging
from enum import IntEnum
from typing import Any, Iterator, List, Tuple, Union

import discord

from .interactions import InteractionCallbackType, InteractionResponse

__all__ = (
    "ButtonStyle",
    "Component",
    "Button",
    "InteractionButton",
)

log = logging.getLogger("red.interactions.models.components")


class ButtonStyle(IntEnum):
    blurple = 1
    grey = 2
    green = 3
    red = 4
    link = 5


class Component:
    __slots__ = ("type", "components", "style", "label", "custom_id", "url", "emoji", "disabled")

    def __init__(
        self,
        type: int = 1,
        *,
        components: List["Component"] = [],
        style: ButtonStyle = None,
        label: str = None,
        custom_id: int = None,
        url: str = None,
        emoji: Union[discord.PartialEmoji, str] = None,
        disabled: bool = False,
    ):
        self.type = type
        self.components = components.copy()
        self.style = style
        self.label = label
        self.custom_id = str(custom_id) if custom_id else None
        self.url = url
        self.emoji = emoji
        if emoji and isinstance(emoji, str):
            self.emoji = discord.PartialEmoji(name=emoji)
        self.disabled = disabled

    def __repr__(self):
        kwargs = " ".join(
            f"{k}={v!r}" for k, v in self.get_slotted_items() if v and not k.startswith("_")
        )
        return f"<{type(self).__name__} {kwargs}>"

    def to_dict(self):
        data = {"type": self.type}
        if self.type == 1:
            data["components"] = [c.to_dict() for c in self.components]
        else:  # elif type == 2:
            data["style"] = self.style.value
            if self.label:
                data["label"] = self.label
            if self.custom_id:
                data["custom_id"] = self.custom_id
            if self.url:
                data["url"] = self.url
            if self.emoji:
                data["emoji"] = self.emoji.to_dict()
            if self.disabled:
                data["disabled"] = self.disabled
        return data

    @classmethod
    def from_dict(cls, data: dict):
        type = data.pop["type"]
        components = [cls.from_dict(c) for c in data.get("components", [])]
        style = ButtonStyle(data.get("style"), 1)
        label = data.get("label")
        custom_id = data.get("custom_id")
        url = data.get("url")
        return cls(
            type, components=components, style=style, label=label, custom_id=custom_id, url=url
        )

    def get_slotted_items(self) -> Iterator[Tuple[str, Any]]:
        for slot in self.__slots__:
            yield slot, getattr(self, slot)


class Button(Component):
    def __init__(self, **kwargs):
        super().__init__(2, **kwargs)


class InteractionButton(InteractionResponse):
    __slots__ = ("custom_id", "component_type", "message")

    def __init__(self, *, state: "InteractionState", data: dict):
        super().__init__(state=state, data=data)
        interaction_data = self.interaction_data
        self.custom_id = interaction_data["custom_id"]
        self.component_type = interaction_data["component_type"]

        message = data["message"]
        if reference := message.get("message_reference"):
            if "channel_id" not in reference:
                reference["channel_id"] = self.channel_id
                # used if dislash is loaded since Message.reference creation
                # pops channel_id from the message_reference dict

        try:
            self.message = discord.Message(
                channel=self.channel, data=message, state=self._discord_state
            )
        except Exception as exc:
            log.exception("An error occured while creating the message for %r", self, exc_info=exc)
            self.message = None

    async def defer_update(self, *, hidden: bool = False):
        flags = 64 if hidden else None
        initial = not self.sent
        data = await self.http.send_message(
            self._token,
            self.id,
            type=InteractionCallbackType.deferred_update_message,
            initial_response=initial,
            flags=flags,
        )
        if not self.sent:
            self.sent = True
        self.deferred = True
        return data

    async def update(
        self,
        content: str = None,
        *,
        embed: discord.Embed = None,
        embeds: List[discord.Embed] = [],
        tts: bool = False,
        allowed_mentions: discord.AllowedMentions = None,
        hidden: bool = False,
        delete_after: int = None,
        components: List[Component] = None,
    ):
        flags = 64 if hidden else None
        initial = not self.sent
        if initial:
            data = await self.http.send_message(
                self._token,
                self.id,
                type=InteractionCallbackType.update_message,
                initial_response=initial,
                content=content,
                embed=embed,
                embeds=embeds,
                allowed_mentions=allowed_mentions,
                tts=tts,
                flags=flags,
                components=components,
            )
            self.sent = True
        else:
            data = await self.http.edit_message(
                self._token,
                content=content,
                embed=embed,
                embeds=embeds,
                allowed_mentions=allowed_mentions,
                components=components,
                original=True,
            )

        if not self.completed:
            self.completed = True
