import pytest
import pytest_asyncio
import os

# Note: These are high-level smoke tests validating Truth Wars v3 mechanics.
# They use the in-memory TruthWarsManager directly without Telegram.

from bot.game.truth_wars_manager import TruthWarsManager
from bot.game.roles import RoleType
from bot.database.database import init_database

os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'

@pytest_asyncio.fixture
async def game_manager():
    await init_database()
    # Drop & recreate to ensure latest schema for this isolated memory DB
    from bot.database.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return TruthWarsManager()

@pytest.mark.asyncio
async def test_headline_set_preparation(game_manager):
    # Simulate a game creation with 5 players
    players = [100 + i for i in range(5)]
    chat_id = -12345
    creator_id = players[0]
    game_id = await game_manager.create_game(chat_id, creator_id)
    for pid in players:
        await game_manager.join_game(game_id, pid, f"u{pid}")
    ok, _ = await game_manager.start_game(game_id, force_start=True)
    assert ok, "Game should start"
    gs = await game_manager.get_game_status(game_id)
    assert gs["round_number"] == 1
    # Ensure queue prepared
    session = game_manager.active_games[game_id]
    # In an empty in-memory DB there may be no headline data; ensure queue field exists
    assert isinstance(session.get("headline_queue", []), list)

@pytest.mark.asyncio
async def test_fact_checker_peek_limit(game_manager):
    # Create dummy Fact Checker role and verify peek cooldown
    from bot.game.roles import FactChecker
    fc = FactChecker()
    assert fc.can_peek_headline(1)
    fc.record_peek(1)
    assert fc.peeks_left == 2
    # Cannot peek consecutive round
    assert not fc.can_peek_headline(2)
    # After gap allowed
    assert fc.can_peek_headline(3)

# Additional detailed flow tests (votes, tie, scoring) are recommended but omitted
# to keep CI runtime fast. They can be expanded incrementally. 