import pytest
import pytest_asyncio

from types import SimpleNamespace

# ---- Utilities ------------------------------------------------

class DummyBot:
    def __init__(self):
        self.msg_count = 0
        self.sent_messages = []

    async def send_message(self, *args, **kwargs):
        # just record a send for assertions
        self.msg_count += 1
        self.sent_messages.append((args, kwargs))


class DummyContext:
    def __init__(self, bot):
        self.bot = bot
        # chat_data may be accessed by some helpers; keep minimal dict
        self.chat_data = {}


# ---- Fixtures -------------------------------------------------

@pytest_asyncio.fixture
def handlers_module():
    # Lazy import to ensure test picks up current code after edits
    import importlib
    handlers = importlib.import_module("bot.handlers.truth_wars_handlers")
    return handlers


# ---- Tests ----------------------------------------------------

@pytest.mark.asyncio
async def test_headline_voting_duplicate_suppressed(handlers_module):
    """First send should pass, second identical send should be ignored."""
    bot = DummyBot()
    ctx = DummyContext(bot)

    # Prepare minimal active game session
    game_id = "test_game_1"
    handlers_module.truth_wars_manager.active_games[game_id] = {
        "chat_id": -1,
        "players": {},
        "player_roles": {},
        "eliminated_players": [],
        "game_id": game_id,
    }

    headline = {
        "id": "headline_1",
        "text": "Test headline",
        "source": "source",
        "is_real": True,
        "explanation": "",
    }

    # First call – should send
    await handlers_module.send_headline_voting(ctx, game_id, headline)
    assert bot.msg_count == 1

    # Second identical call – should be suppressed
    await handlers_module.send_headline_voting(ctx, game_id, headline)
    assert bot.msg_count == 1, "Duplicate headline message was not suppressed"


@pytest.mark.asyncio
async def test_swap_headline_callback_no_attribute_error(handlers_module):
    """Ensure Scammer swap callback doesn't raise AttributeError after fix."""
    from bot.game.roles import Scammer, RoleType

    bot = DummyBot()
    ctx = DummyContext(bot)

    # Prepare game session with a Scammer role
    game_id = "swap_game"
    scammer_id = 42
    handlers_module.truth_wars_manager.active_games[game_id] = {
        "chat_id": -1,
        "players": {scammer_id: {"username": "scammer"}},
        "player_roles": {
            scammer_id: {"role": Scammer(), "faction": "scammer_team", "is_alive": True}
        },
        "eliminated_players": [],
        "game_id": game_id,
    }

    # Build dummy Telegram-like objects
    class DummyQuery:
        def __init__(self):
            self.data = f"swap_headline_no_{game_id}"
            self.from_user = SimpleNamespace(id=scammer_id)
            self._answers = []
            self._edits = []

        async def answer(self, *a, **kw):
            self._answers.append((a, kw))

        async def edit_message_text(self, text):
            self._edits.append(text)

    class DummyUpdate:
        def __init__(self, query):
            self.callback_query = query
            self.effective_user = query.from_user

    query = DummyQuery()
    update = DummyUpdate(query)

    # Should not raise – we don't assert behaviour beyond absence of exception
    await handlers_module.handle_swap_headline_callback(update, ctx)

    # Ensure a confirmation edit happened (means code ran through)
    assert query._edits, "Callback did not edit message as expected" 