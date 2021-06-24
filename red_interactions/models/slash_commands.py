import logging
from enum import IntEnum
from typing import Dict, List, Union

import discord

from .interactions import InteractionResponse

__all__ = (
    "UnknownCommand",
    "SlashOptionType",
    "ResponseOption",
    "InteractionCommand",
    "SlashOptionChoice",
    "SlashOption",
    "SlashCommand",
)

log = logging.getLogger("red.interactions.models.slash_commands")


class UnknownCommand:
    __slots__ = ("id",)
    cog = None

    def __init__(self, *, id: int = None):
        self.id = id

    def __repr__(self) -> str:
        return f"UnknownCommand(id={self.id})"

    @property
    def name(self):
        return self.__repr__()

    @property
    def qualified_name(self):
        return self.__repr__()

    def __bool__(self) -> bool:
        return False


class SlashOptionType(IntEnum):
    """
    +---------+-------------------------------------------------------------------------------------------------------+----------------------+--------------------------------------------+
    | Type    | Description                                                                                           | Example              | Adapter                                    |
    +=========+=======================================================================================================+======================+============================================+
    | String  | Accepts any user inputted text as an argument.                                                        | ``{string}``         | :doc:`StringAdapter <tse:adapter>`         |
    +---------+-------------------------------------------------------------------------------------------------------+----------------------+--------------------------------------------+
    | Integer | Only allows number input for the argument.                                                            | ``{integer}``        | :doc:`IntAdapter <tse:adapter>`            |
    +---------+-------------------------------------------------------------------------------------------------------+----------------------+--------------------------------------------+
    | Boolean | Allows either ``True`` or ``False`` as input.                                                         | ``{boolean}``        | :doc:`StringAdapter <tse:adapter>`         |
    +---------+-------------------------------------------------------------------------------------------------------+----------------------+--------------------------------------------+
    | User    | Refers to a member of the server or a member in the DM channel, accepting username or IDs as input.   | ``{user(name)}``     | :doc:`MemberAdapter <tse:adapter>`         |
    +---------+-------------------------------------------------------------------------------------------------------+----------------------+--------------------------------------------+
    | Channel | Refers to a text, voice, or category channel in this server, accepting channel names or IDs as input. | ``{channel(topic)}`` | :doc:`ChannelAdapter <tse:adapter>`        |
    +---------+-------------------------------------------------------------------------------------------------------+----------------------+--------------------------------------------+
    | Role    | Refers to a server role, accepting role name or IDs as input.                                         | ``{role(id)}``       | :doc:`SafeObjectAdapter <tse:adapter>`     |
    +---------+-------------------------------------------------------------------------------------------------------+----------------------+--------------------------------------------+
    | Choices | Offers a list of choices for the user to pick.                                                        | ``{choice}``         | :doc:`StringAdapter <tse:adapter>`         |
    |         | Each option has a name and underlying value which is returned as string argument when accessed.       |                      |                                            |
    +---------+-------------------------------------------------------------------------------------------------------+----------------------+--------------------------------------------+
    """

    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8


class ResponseOption:
    __slots__ = ("type", "name", "value")

    def __init__(self, *, type: SlashOptionType, name: str, value: str):
        self.type = type
        self.name = name
        self.value = value

    def set_value(self, value):
        self.value = value

    def __repr__(self):
        return f"<ResponseOption type={self.type!r} name={self.name!r} value={self.value!r}>"

    @classmethod
    def from_dict(cls, data: dict):
        type = SlashOptionType(data.get("type", 3))
        return cls(type=type, name=data["name"], value=data["value"])


class SlashOptionChoice:
    __slots__ = ("name", "value")

    def __init__(self, name: str, value: Union[str, int]):
        self.name = name
        self.value = value

    def to_dict(self):
        return {"name": self.name, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data["name"], data["value"])


class SlashOption:
    __slots__ = ("type", "name", "description", "required", "choices", "options")

    def __init__(
        self,
        *,
        option_type: SlashOptionType = SlashOptionType.STRING,
        name: str,
        description: str,
        required: bool = False,
        choices: List[SlashOptionChoice] = [],
        options: list = [],
    ):
        if not isinstance(option_type, SlashOptionType):
            option_type = SlashOptionType(option_type)
        self.type = option_type
        self.name = name
        self.description = description
        self.required = required
        self.choices = choices.copy()
        self.options = options.copy()

    def __str__(self):
        return self.name

    def __repr__(self):
        values = ["name", "type", "required"]
        if self.choices:
            values.append("choices")
        if self.options:
            values.append("options")
        inner = " ".join(f"{value}={getattr(self, value)!r}" for value in values)
        return f"<SlashOption {inner}>"

    def to_dict(self):
        data = {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "required": self.required,
        }

        if self.choices:
            data["choices"] = [c.to_dict() for c in self.choices]
        if self.options:
            data["options"] = [o.to_dict() for o in self.options]
        return data

    @classmethod
    def from_dict(cls, data: dict):
        choices = [SlashOptionChoice.from_dict(choice) for choice in data.get("choices", [])]

        options = [cls.from_dict(option) for option in data.get("options", [])]
        return cls(
            option_type=SlashOptionType(data["type"]),
            name=data["name"],
            description=data["description"],
            required=data.get("required", False),
            choices=choices,
            options=options,
        )


class SlashCommand:
    __slots__ = (
        "state",
        "http",
        "id",
        "application_id",
        "name",
        "description",
        "guild_id",
        "options",
    )

    def __init__(
        self,
        state: "InteractionState",
        *,
        id: int = None,
        application_id: int = None,
        name: str,
        description: str,
        guild_id: int = None,
        options: List[SlashOption] = [],
    ):
        self.state = state
        self.http = state.http

        self.id = id
        self.application_id = application_id
        self.name = name
        self.description = description
        self.guild_id = guild_id
        self.options = options.copy()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        members = ("id", "name", "description", "options", "guild_id")
        attrs = " ".join(f"{member}={getattr(self, member)!r}" for member in members)
        return f"<SlashCommand {attrs}>"

    @property
    def qualified_name(self) -> str:
        return self.name

    def to_request(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "options": [o.to_dict() for o in self.options],
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "application_id": self.application_id,
            "name": self.name,
            "description": self.description,
            "options": [o.to_dict() for o in self.options],
            "guild_id": self.guild_id,
        }

    @classmethod
    def from_dict(cls, state: "InteractionState", data: dict):
        id = discord.utils._get_as_snowflake(data, "id")
        application_id = discord.utils._get_as_snowflake(data, "application_id")
        name = data["name"]
        description = data["description"]
        options = [SlashOption.from_dict(o) for o in data.get("options", [])]
        guild_id = discord.utils._get_as_snowflake(data, "guild_id")
        return cls(
            state,
            id=id,
            application_id=application_id,
            name=name,
            description=description,
            guild_id=guild_id,
            options=options,
        )

    async def save_config(self):
        async with self.state.config.commands() as commands:
            commands[self.id] = self.to_dict()

    def _parse_response_data(self, data: dict):
        _id = discord.utils._get_as_snowflake(data, "id")
        application_id = discord.utils._get_as_snowflake(data, "application_id")
        name = data.get("name")
        description = data.get("description")
        if _id:
            self.id = _id
        if application_id:
            self.application_id = application_id
        if name:
            self.name = name
        if description:
            self.description = description
        self.options = [SlashOption.from_dict(o) for o in data.get("options", [])]

    async def register(self):
        if self.guild_id:
            data = await self.http.add_guild_slash_command(self.guild_id, self.to_request())
        else:
            data = await self.http.add_slash_command(self.to_request())
        self._parse_response_data(data)
        await self.save_config()
        self.add_to_cache()

    async def edit(
        self, *, name: str = None, description: str = None, options: List[SlashOption] = None
    ):
        payload = {}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        if options:
            payload["options"] = [o.to_dict() for o in options]

        if self.guild_id:
            data = await self.http.edit_guild_slash_command(self.guild_id, self.id, payload)
        else:
            data = await self.http.edit_slash_command(self.id, payload)
        self._parse_response_data(data)

    async def delete(self):
        self.remove_from_cache()
        if self.guild_id:
            await self.http.remove_guild_slash_command(self.guild_id, self.id)
        else:
            await self.http.remove_slash_command(self.id)
        async with self.state.config.commands() as commands:
            try:
                del commands[self.id]
            except KeyError:
                pass

    def add_to_cache(self):
        self.state.command_cache[self.id] = self

    def remove_from_cache(self):
        try:
            del self.state.command_cache[self.id]
        except KeyError:
            pass


class InteractionCommand(InteractionResponse):
    __slots__ = ("command_name", "command_id", "options", "_cs_content")

    def __init__(self, *, state: "InteractionState", data: dict):
        super().__init__(state=state, data=data)
        self.command_name = self.interaction_data["name"]
        self.command_id = int(self.interaction_data["id"])
        self.options: List[ResponseOption] = []
        self._parse_options(
            self.interaction_data.get("options", []), self.interaction_data.get("resolved", {})
        )

    def __repr__(self) -> str:
        return f"<{type(self).__name__} id={self.id} command={self.command!r} options={self.options!r} channel={self.channel!r} author={self.author!r}>"

    @discord.utils.cached_slot_property("_cs_content")
    def content(self):
        items = [f"/{self.command_name}"]
        for option in self.options:
            items.append(f"`{option.name}: {option.value}`")
        return " ".join(items)

    @property
    def command(self) -> Union[SlashCommand, UnknownCommand]:
        return self.state.get_command(self.command_id) or UnknownCommand(id=self.command_id)

    @property
    def jump_url(self):
        guild_id = getattr(self.guild, "id", "@me")
        return f"https://discord.com/channels/{guild_id}/{self.channel_id}/{self.id}"

    def _parse_options(self, options: List[dict], resolved: Dict[str, Dict[str, dict]]):
        for o in options:
            option = ResponseOption.from_dict(o)
            handler_name = f"_handle_option_{option.type.name.lower()}"
            try:
                handler = getattr(self, handler_name)
            except AttributeError:
                pass
            else:
                try:
                    option = handler(o, option, resolved)
                except Exception as error:
                    log.exception(
                        "Failed to handle option data for option:\n%r", o, exc_info=error
                    )
            self.options.append(option)

    def _handle_option_channel(
        self, data: dict, option: ResponseOption, resolved: Dict[str, Dict[str, dict]]
    ):
        channel_id = int(data["value"])
        resolved_channel = resolved["channels"][data["value"]]
        if self.guild_id:
            if channel := self.guild.get_channel(channel_id):
                pass
            else:
                channel = discord.TextChannel(
                    state=self._discord_state, guild=self.guild, data=resolved_channel
                )
        else:
            if channel := self._discord_state._get_private_channel(channel_id):
                pass
            else:
                channel = discord.DMChannel(
                    state=self._discord_state, me=self.bot.user, data=resolved_channel
                )
        option.set_value(channel)
        return option

    def _handle_option_user(
        self, data: dict, option: ResponseOption, resolved: Dict[str, Dict[str, dict]]
    ):
        user_id = int(data["value"])
        resolved_user = resolved["users"][data["value"]]
        if self.guild_id:
            if user := self.guild.get_member(user_id):
                pass
            else:
                user = discord.Member(
                    guild=self.guild, data=resolved_user, state=self._discord_state
                )
                self.guild._add_member(user)
        else:
            user = self._discord_state.store_user(resolved_user)
        option.set_value(user)
        return option

    def _handle_option_role(
        self, data: dict, option: ResponseOption, resolved: Dict[str, Dict[str, dict]]
    ):
        role_id = int(data["value"])
        resolved_role = resolved["roles"][data["value"]]
        if self.guild_id:
            if role := self.guild.get_role(role_id):
                pass
            else:
                role = discord.Role(guild=self.guild, data=resolved_role, state=self)
                self.guild._add_role(role)
            option.set_value(role)
        return option

    def to_reference(self, *args, **kwargs):
        # return None to prevent reply since interaction responses already reply (visually)
        # additionally, replying to an interaction response raises
        # message_reference: Unknown message
        return

    @property
    def me(self):
        return self.guild.me if self.guild else self.bot.user
