# Truth Wars v3 – Implementation Guide

This document maps the new **v3 rule-set** to concrete engineering tasks for the existing Python/Telegram code-base.

---

## 1. Overview of Required Changes

1. **Game State** – add new fields for *scores*, *roundCounter*, *headlineSet*, *factCheckerPeekCooldown*.
2. **Headline Logic** – create `prepare_headline_set()` that builds Set A & B, shuffles, stores chosen set.
3. **Role System** – update `roles.py` to include `fact_checker_peeks_left` and `peek_cooldown` flags.
4. **Phase Manager** – refactor `truth_wars_manager.py` to follow the 7-step Round Structure.
5. **Persistence** – DB already stores players & roles; extend with `team_score` (Truth / Scam) and `shadow_banned` boolean.

---

## 2. Data Structures

```python
# bot/game/refined_game_states.py
@dataclass
class TruthWarsState:
    round_no: int = 1
    headlines: List[Headline]
    scores: dict[str, int] = field(default_factory=lambda: {"truth": 0, "scam": 0})
    fact_checker_peeks_left: int = 3
    fact_checker_cooldown: bool = False
    snipe_used: bool = False
```
*Add `Headline` as a light model with `text`, `is_real`, and `revealed` flags.*

---

## 3. Phase Flow (truth_wars_manager.py)

```text
start_round -> reveal_headline -> discussion_timer(180s) ->
    handle_fact_checker_peek() -> collect_votes() ->
    optional_fact_checker_snipe() -> shadow_ban_vote() ->
    update_scores() -> check_end_conditions() -> next_round()
```
Key helper functions to create/modify:
* `handle_fact_checker_peek(user_id)` – enforce cooldown logic.
* `apply_snipe(target_id)` – validate round 1-4, single use.
* `shadow_ban_vote()` – manage tie-break and state updates.
* `tally_votes()` – decide majority & apply Section 4 scoring rules.
* `check_end_conditions()` – trigger win / tie events.

---

## 4. Bot Interface Updates

1. **Phase Tracker** – send a message at each step (`Enum Phase`).
2. **Inline Buttons**
   * *Trust* / *Flag* – during Initial Vote.
   * *Peek* / *Skip* – DM to Fact-Checker at discussion start.
   * *Snipe* – DM to Fact-Checker after voting (Rounds 1-4).
   * *Shadow Ban* – group poll or simple text votes.
   * *Continue* – host-only button to advance to next round.
3. **Error Handling** – reject late votes, second peeks, invalid snipes.

---

## 5. Database Migration (SQLite)

```sql
ALTER TABLE players ADD COLUMN shadow_banned BOOLEAN DEFAULT 0;
ALTER TABLE game_state ADD COLUMN truth_score INTEGER DEFAULT 0;
ALTER TABLE game_state ADD COLUMN scam_score  INTEGER DEFAULT 0;
```
No new tables needed; headlines can remain in JSON within game_state or be normalised later.

---

## 6. Tests to Add (tests/)

1. `test_prepare_headline_set_balance()` – validates 3/2 or 2/3 distribution.
2. `test_vote_tie_results_in_no_points()`.
3. `test_fact_checker_cooldown()` – cannot peek in consecutive rounds.
4. `test_single_snipe_limit()` – 2nd call rejected.
5. `test_end_conditions()` – covers all win paths and tie path.

---

## 7. Roll-out Plan

1. Implement feature branches in order: *data-model ➜ headline logic ➜ phase flow ➜ bot UI*.
2. Run migrations, seed headline sets in dev DB.
3. Pass new tests & manual telegram play-through (happy path + edge cases).
4. Update README & BotFather commands, tag release `v3.0`.

---

## 8. Future Enhancements

* Web dashboard to edit headline pools.
* Analytics on voting accuracy for each user.
* Difficulty presets that tweak peek limit & hint accuracy. 