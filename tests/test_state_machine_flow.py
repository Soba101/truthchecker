import pytest
from datetime import datetime, timedelta, timezone

from bot.game.refined_game_states import RefinedGameStateMachine, PhaseType


def _fast_forward(sm):
    """Helper: move the phase_start_time back so can_transition() becomes True."""
    sm.phase_start_time = datetime.now(timezone.utc) - timedelta(
        seconds=sm.phase_durations.get(sm.current_phase, 300) + 1
    )


def _build_base_game_state():
    """Return a minimal game_state dict with permissive flags for transitions."""
    return {
        # Lobby flags
        "force_start": True,
        # Role assignment flags
        "all_roles_assigned": True,
        # Voting/discussion flags
        "all_eligible_voted": True,
        # Win-condition counters
        "rounds_completed": 0,
        "fake_headlines_trusted": 0,
        "fake_headlines_flagged": 0,
        # Faction / reputation maps (empty but present)
        "player_roles": {
            1: {"role": __import__("bot.game.roles", fromlist=["FactChecker"]).FactChecker()},
            2: {"role": __import__("bot.game.roles", fromlist=["Scammer"]).Scammer()},
        },
        "shadow_banned_players": {},
        "player_reputation": {},
        "eliminated_players": [],
        # Snipe shortcut so we skip the PLAYER_VOTING phase for brevity
        "snipe_used_this_round": True,
    }


def _advance(sm, gs):
    """Fast-forward the clock then attempt a transition."""
    _fast_forward(sm)
    return sm.transition_phase(gs)


def test_full_game_flow_until_game_end():
    """Drive the state-machine through five rounds and assert GAME_END is reached."""
    sm = RefinedGameStateMachine()
    gs = _build_base_game_state()

    # Step once to leave lobby → role_assignment
    _advance(sm, gs)
    assert sm.current_phase == PhaseType.ROLE_ASSIGNMENT

    # Loop until GAME_END or safeguard iterations
    safety_counter = 0
    while sm.current_phase != PhaseType.GAME_END and safety_counter < 50:
        safety_counter += 1
        # If we just finished ROUND_RESULTS, increment rounds_completed
        if sm.current_phase == PhaseType.ROUND_RESULTS:
            gs["rounds_completed"] += 1
        _advance(sm, gs)

    assert sm.current_phase == PhaseType.GAME_END, "State machine should reach GAME_END"
    # After normal play we expect exactly 5 rounds completed
    assert gs["rounds_completed"] >= 5
    assert sm.round_number >= 5 