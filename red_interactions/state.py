from typing import Dict

from redbot.core.bot import Red

from .http import InteractionsHTTPClient
from .models import SlashCommand

__all__ = ("InteractionState",)


class InteractionState:
    __slots__ = ("bot", "application_id", "http", "command_cache")

    def __init__(self, bot: Red, application_id: int):
        self.bot = bot
        self.application_id = application_id
        self.http = InteractionsHTTPClient(self)
        self.command_cache: Dict[int, SlashCommand] = {}

    def get_command(self, command_id: int, /) -> SlashCommand:
        return self.command_cache.get(command_id)
