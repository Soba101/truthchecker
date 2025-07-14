import pytest
from datetime import datetime, timedelta, timezone

from bot.game.refined_game_states import RefinedGameStateMachine, PhaseType
from bot.game.roles import FactChecker, Scammer, Normie

# ========= Helpers ==========

def _sm_in_phase(phase: PhaseType):
    sm = RefinedGameStateMachine()
    sm.current_phase = phase
    sm.phase_start_time = datetime.now(timezone.utc)  # irrelevant for direct handler calls
    return sm


def _base_game_state():
    # Provide baseline structures with two players, one in each faction
    return {
        "player_roles": {
            1: {"role": FactChecker()},
            2: {"role": Scammer()},
        },
        "shadow_banned_players": {},
        "player_reputation": {1: 3, 2: 3},
        "eliminated_players": [],
    }

# ========= Tests ============

def test_discussion_message_valid_and_invalid():
    sm = _sm_in_phase(PhaseType.DISCUSSION)
    gs = _base_game_state()

    # Empty message -> fail
    result = sm.handle_action("send_message", 1, {"message": "   "}, gs)
    assert result["success"] is False

    # Over-length message -> fail
    long_text = "x" * 501
    result = sm.handle_action("send_message", 1, {"message": long_text}, gs)
    assert result["success"] is False

    # Shadow-banned user -> fail
    gs["shadow_banned_players"][1] = True
    result = sm.handle_action("send_message", 1, {"message": "Hello"}, gs)
    assert result["success"] is False

    # Valid message from unbanned user -> success
    gs["shadow_banned_players"].pop(1)
    result = sm.handle_action("send_message", 1, {"message": "Hello"}, gs)
    assert result["success"] is True


def test_headline_vote_validation():
    sm = _sm_in_phase(PhaseType.VOTING)
    gs = _base_game_state()
    gs.update({
        "Elimination_players": [],
        "player_reputation": {1: 3},
        "shadow_banned_players": {},
    })

    # Invalid vote choice
    result = sm.handle_action("vote_headline", 1, {"vote_type": "maybe"}, gs)
    assert result["success"] is False

    # Eliminated players cannot vote
    gs["eliminated_players"].append(1)
    result = sm.handle_action("vote_headline", 1, {"vote_type": "trust"}, gs)
    assert result["success"] is False
    gs["eliminated_players"].remove(1)

    # Shadow banned cannot vote
    gs["shadow_banned_players"][1] = True
    result = sm.handle_action("vote_headline", 1, {"vote_type": "trust"}, gs)
    assert result["success"] is False
    gs["shadow_banned_players"].pop(1)

    # Valid vote
    result = sm.handle_action("vote_headline", 1, {"vote_type": "trust"}, gs)
    assert result["success"] is True


def test_snipe_attempt_success_and_failure():
    sm = _sm_in_phase(PhaseType.SNIPE_OPPORTUNITY)
    gs = _base_game_state()

    # Successful snipe: FactChecker snipes Scammer
    result = sm.handle_action("snipe_player", 1, {"target_id": 2}, gs)
    assert result["success"] is True
    assert result["effect"] == "shadow_ban_target"

    # Failed snipe: FactChecker targets innocent Normie
    # Provide fresh FactChecker (unused snipe) for second attempt
    gs["player_roles"][1]["role"] = FactChecker()
    gs["player_roles"][3] = {"role": Normie()}
    result = sm.handle_action("snipe_player", 1, {"target_id": 3}, gs)
    assert result["success"] is False
    assert result["effect"] == "shadow_ban_self" 