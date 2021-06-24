import logging

from redbot.core import Config
from redbot.core.bot import Red

from ._state import InteractionState

__all__ = (
    "is_initialized",
    "state",
    "set_application_id",
    "get_application_id",
    "initialize",
    "teardown",
    "config",
)

log = logging.getLogger("red.interactions")

_initialized = False
_state: InteractionState = None
config = Config.get_conf(
    None, 3274508972347578923, force_registration=True, cog_name="Red-Interactions"
)
config.register_global(application_id=None, commands={})


def is_initialized() -> bool:
    return _initialized


def state() -> InteractionState:
    return _state


async def set_application_id(application_id: int):
    await config.application_id.set(application_id)


async def get_application_id(bot: Red) -> int:
    application_id = await config.application_id()
    if application_id:
        return application_id
    application_id = (await bot.application_info()).id
    await set_application_id(application_id)
    return application_id


async def initialize(bot: Red, *, application_id: int = None) -> InteractionState:
    """
    Initialize the interactions module with a bot.
    """
    log.debug("initializing module")
    global _state
    global _initialized

    if _initialized:
        raise RuntimeError(f"Red-Interactions has already been initialized with {_state!r}")

    if application_id is None:
        application_id = await get_application_id(bot)
    _state = InteractionState(bot, application_id, config)
    await _state.cache_commands()
    _initialized = True
    return _state


async def teardown():
    await _state.teardown()
