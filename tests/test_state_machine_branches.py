import types
from datetime import datetime, timedelta, timezone

import pytest

from bot.game.refined_game_states import RefinedGameStateMachine, PhaseType
from bot.game.roles import FactChecker, Scammer, Influencer


# ====================
# Helper utilities
# ====================

def _fast_forward(sm: RefinedGameStateMachine):
    """Force current phase to expire so can_transition()==True."""
    sm.phase_start_time = datetime.now(timezone.utc) - timedelta(
        seconds=sm.phase_durations.get(sm.current_phase, 300) + 1
    )


def _minimal_game_state(**kwargs):
    """Return a base game_state dict, allowing overrides via kwargs."""
    base = {
        "force_start": True,
        "all_roles_assigned": True,
        "all_eligible_voted": True,
        "rounds_completed": 0,
        "fake_headlines_trusted": 0,
        "fake_headlines_flagged": 0,
        "player_roles": {
            1: {"role": FactChecker()},
            2: {"role": Scammer()},
        },
        "shadow_banned_players": {},
        "player_reputation": {},
        "eliminated_players": [],
        "snipe_used_this_round": False,  # default to False so PLAYER_VOTING is exercised
    }
    base.update(kwargs)
    return base


def _advance(sm: RefinedGameStateMachine, gs: dict):
    _fast_forward(sm)
    return sm.transition_phase(gs)


# ====================
# Tests
# ====================

@pytest.mark.asyncio
async def test_snipe_to_player_voting_branch():
    """Verify flow: ROUND_RESULTS ➜ SNIPE_OPPORTUNITY ➜ PLAYER_VOTING ➜ HEADLINE_REVEAL."""
    sm = RefinedGameStateMachine()
    gs = _minimal_game_state()

    # Skip ahead: pretend we are finishing round 2 (eligible for snipe phase)
    sm.round_number = 2
    sm.current_phase = PhaseType.ROUND_RESULTS

    # 1️⃣ ROUND_RESULTS → SNIPE_OPPORTUNITY
    _advance(sm, gs)
    assert sm.current_phase == PhaseType.SNIPE_OPPORTUNITY

    # 2️⃣ No snipe used; SNIPE_OPPORTUNITY → PLAYER_VOTING
    _advance(sm, gs)
    assert sm.current_phase == PhaseType.PLAYER_VOTING

    # 3️⃣ PLAYER_VOTING → HEADLINE_REVEAL (next round)
    _advance(sm, gs)
    assert sm.current_phase == PhaseType.HEADLINE_REVEAL
    assert sm.round_number == 3


def test_win_condition_scammer_trust():
    """Game should end if 3 fake headlines were trusted."""
    sm = RefinedGameStateMachine()
    gs = _minimal_game_state(fake_headlines_trusted=3)
    sm.round_number = 3
    sm.current_phase = PhaseType.ROUND_RESULTS

    _advance(sm, gs)
    assert sm.current_phase == PhaseType.GAME_END


def test_win_condition_truth_flagged():
    """Game should end if 3 fake headlines were flagged."""
    sm = RefinedGameStateMachine()
    gs = _minimal_game_state(fake_headlines_flagged=3)
    sm.round_number = 3
    sm.current_phase = PhaseType.ROUND_RESULTS

    _advance(sm, gs)
    assert sm.current_phase == PhaseType.GAME_END


def test_force_transition_skips_timer():
    """force_transition should move to requested phase regardless of timers."""
    sm = RefinedGameStateMachine()
    gs = _minimal_game_state()

    result = sm.force_transition(PhaseType.DISCUSSION, gs)
    assert result["success"] is True
    assert sm.current_phase == PhaseType.DISCUSSION

    # Confirm we can still advance normally afterward
    _advance(sm, gs)
    assert sm.current_phase == PhaseType.VOTING 