import logging
from typing import Dict, Optional

from redbot.core import Config
from redbot.core.bot import Red

from .http import InteractionsHTTPClient
from .models import InteractionButton, InteractionCommand, SlashCommand

__all__ = ("InteractionState",)

log = logging.getLogger("red.interactions.state")


class InteractionState:
    __slots__ = ("bot", "application_id", "http", "command_cache", "config")

    def __init__(self, bot: Red, application_id: int, config: Config):
        self.bot = bot
        self.application_id = application_id
        self.http = InteractionsHTTPClient(self)
        self.command_cache: Dict[int, SlashCommand] = {}
        self.config = config

        bot._connection.parsers["INTERACTION_CREATE"] = self.parse_interaction_create

    def __repr__(self):
        return f"<{type(self).__name__} application_id={self.application_id} command_count={len(self.command_cache)}>"

    async def cache_commands(self):
        commands = await self.config.commands()
        for command_data in commands.values():
            command = SlashCommand.from_dict(self, command_data)
            command.add_to_cache()

    def get_command(self, command_id: int, /) -> Optional[SlashCommand]:
        return self.command_cache.get(command_id)

    async def teardown(self):
        del self.bot._connection.parsers["INTERACTION_CREATE"]

    def parse_interaction_create(self, data: dict):
        log.debug("Interaction data received:\n%r", data)
        handlers = {2: self.handle_slash_interaction, 3: self.handle_button_interaction}
        handler = handlers.get(data["type"], self.handle_slash_interaction)
        try:
            handler(data)
        except Exception as e:
            log.exception(
                "An exception occured while handling an interaction:\n%r", data, exc_info=e
            )

    def handle_slash_interaction(self, data: dict):
        interaction = InteractionCommand(state=self, data=data)
        self.bot.dispatch("red_slash_interaction", interaction)

    def handle_button_interaction(self, data: dict):
        button = InteractionButton(state=self, data=data)
        self.bot.dispatch("red_button_interaction", button)
