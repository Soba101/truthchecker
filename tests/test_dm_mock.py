import asyncio
import types

import pytest

from bot.game.truth_wars_manager import TruthWarsManager
from bot.game.roles import FactChecker


class _MockBot:
    """Collects outbound messages instead of hitting Telegram."""
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id, text, **kwargs):
        # Store tuple for assertion
        self.sent.append((chat_id, text))


@pytest.mark.asyncio
async def test_fact_checker_dm_flow():
    """Smoke-test that ability activation uses the provided bot context without errors."""
    mgr = TruthWarsManager()

    mock_bot = _MockBot()
    # Using SimpleNamespace so TruthWarsManager sees `.bot`
    mgr.set_bot_context(types.SimpleNamespace(bot=mock_bot))

    # Minimal game_session context required by _activate_fact_checker_ability
    game_session = {
        "round_number": 1,
        "fact_checker_no_info_round": 2,
        "current_headline": {
            "text": "Unit-test headline",
            "is_real": True,
            "explanation": "Mock explanation"
        }
    }

    # Create a dummy Fact Checker role and invoke ability
    fc_role = FactChecker()
    result = await mgr._activate_fact_checker_ability(game_session, user_id=42, role=fc_role)

    # Ability should succeed and send exactly one DM
    assert result["success"] is True
    assert len(mock_bot.sent) == 1
    chat_id, text = mock_bot.sent[0]
    assert chat_id == 42  # DM sent to the requesting user
    assert "Unit-test headline" in text 