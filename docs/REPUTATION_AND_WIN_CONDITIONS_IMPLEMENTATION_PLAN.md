# 🎯 Reputation System & Headline Win Conditions Implementation Plan

## 📋 **Overview**
This document outlines the implementation plan for the core game mechanics missing from the current Truth Wars implementation:
1. **Reputation System** - 3 RP tracking with Ghost Viewer mechanics
2. **Headline-Based Win Conditions** - 3 fake headlines trusted/flagged wins

---

## 🎮 **Reputation System Implementation**

### **Current State**
- ✅ Database models exist (`PlayerReputationHistory`, `GamePlayer.current_reputation`)
- ❌ No actual RP tracking logic in game manager
- ❌ No Ghost Viewer enforcement
- ❌ No RP gain/loss calculations

### **Target Mechanics**
```
Starting RP: 3 for all players
RP Changes:
- Correct vote on real headline (TRUST) → +1 RP
- Correct vote on fake headline (FLAG) → +1 RP  
- Wrong vote on real headline (FLAG) → -1 RP
- Wrong vote on fake headline (TRUST) → -1 RP
- Scammer bonus: When majority votes wrong → +1 RP

Ghost Viewer Status:
- 0 RP → Can watch game, cannot vote, cannot use abilities
- RP cannot go below 0
- RP has no upper limit
```

### **Implementation Steps**

#### **Step 1: Add RP Tracking to Game Session**
```python
# Add to game_session initialization
game_session["player_reputation"] = {
    player_id: 3 for player_id in game_session["players"]
}
game_session["headline_results"] = {
    "fake_headlines_trusted": 0,
    "fake_headlines_flagged": 0,
    "real_headlines_trusted": 0,
    "real_headlines_flagged": 0
}
```

#### **Step 2: Implement RP Calculation Logic**
```python
async def _update_player_reputation(self, game_session: Dict, vote_results: Dict) -> None:
    """
    Update player reputation based on voting results.
    
    Args:
        game_session: Current game session
        vote_results: Dict with voting outcomes and headline truth value
    """
    # Calculate RP changes for each voter
    # Log reputation history to database
    # Update player_reputation in session
    # Check for Ghost Viewer status changes
```

#### **Step 3: Implement Ghost Viewer Enforcement**
```python
def _can_player_vote(self, game_session: Dict, player_id: int) -> bool:
    """Check if player can vote (not Ghost Viewer)."""
    current_rp = game_session["player_reputation"].get(player_id, 3)
    return current_rp > 0

def _can_player_use_ability(self, game_session: Dict, player_id: int) -> bool:
    """Check if player can use abilities (not Ghost Viewer)."""
    current_rp = game_session["player_reputation"].get(player_id, 3)
    return current_rp > 0
```

#### **Step 4: Update Voting Resolution Logic**
```python
async def _resolve_voting(self, game_session: Dict) -> None:
    """Enhanced voting resolution with RP updates."""
    # Calculate vote results
    # Determine RP changes
    # Update headline win condition counters
    # Call _update_player_reputation()
    # Check win conditions
```

---

## 🏆 **Headline Win Conditions Implementation**

### **Current State**
- ❌ Using elimination-based win conditions
- ❌ Not tracking fake/real headlines trusted/flagged
- ❌ No progress tracking toward 3 headline goals

### **Target Win Conditions**
```
Scammers Win:
- 3 fake headlines trusted by majority vote
- OR all Truth Seekers eliminated/shadow banned

Truth Team Wins:
- 3 fake headlines flagged correctly by majority vote
- OR all Scammers eliminated/shadow banned
- OR 5 rounds completed without Scammer victory
```

### **Implementation Steps**

#### **Step 1: Add Headline Tracking to Game Session**
```python
# Track progress toward win conditions
game_session["win_progress"] = {
    "fake_headlines_trusted": 0,    # Scammer win condition
    "fake_headlines_flagged": 0,    # Truth team win condition
    "rounds_completed": 0
}
```

#### **Step 2: Update Vote Resolution to Track Headlines**
```python
async def _resolve_voting(self, game_session: Dict) -> None:
    # ... existing code ...
    
    # Update win condition tracking
    if headline_is_fake and majority_trusts:
        game_session["win_progress"]["fake_headlines_trusted"] += 1
    elif headline_is_fake and not majority_trusts:
        game_session["win_progress"]["fake_headlines_flagged"] += 1
    
    # Check for immediate win
    if self._check_headline_win_conditions(game_session):
        self._trigger_game_end(game_session)
```

#### **Step 3: Replace Win Condition Logic**
```python
def _check_headline_win_conditions(self, game_session: Dict) -> bool:
    """Check headline-based win conditions."""
    win_progress = game_session["win_progress"]
    
    # Scammer win: 3 fake headlines trusted
    if win_progress["fake_headlines_trusted"] >= 3:
        game_session["winner"] = "scammers"
        game_session["win_reason"] = "3 fake headlines trusted"
        return True
    
    # Truth team win: 3 fake headlines flagged
    if win_progress["fake_headlines_flagged"] >= 3:
        game_session["winner"] = "truth_seekers"
        game_session["win_reason"] = "3 fake headlines flagged"
        return True
    
    # Truth team win: 5 rounds completed
    if win_progress["rounds_completed"] >= 5:
        game_session["winner"] = "truth_seekers"
        game_session["win_reason"] = "5 rounds completed"
        return True
    
    return False
```

#### **Step 4: Add Progress Display**
```python
def _get_win_progress_display(self, game_session: Dict) -> str:
    """Generate progress display for current win conditions."""
    progress = game_session["win_progress"]
    
    return (
        f"📊 **Win Progress:**\n"
        f"🔴 Scammers: {progress['fake_headlines_trusted']}/3 fake headlines trusted\n"
        f"🔵 Truth Team: {progress['fake_headlines_flagged']}/3 fake headlines flagged\n"
        f"⏱️ Round: {progress['rounds_completed']}/5"
    )
```

---

## 🔧 **Integration Points**

### **Files to Modify**
1. **`bot/game/truth_wars_manager.py`**
   - Add RP tracking initialization
   - Implement RP calculation methods
   - Replace win condition logic
   - Update voting resolution

2. **`bot/game/game_states.py`** or **`bot/game/refined_game_states.py`**
   - Add Ghost Viewer checks in voting phases
   - Update phase transition logic

3. **`bot/handlers/truth_wars_handlers.py`**
   - Add RP display in status messages
   - Enforce Ghost Viewer restrictions

### **Database Integration**
- Log reputation changes to `PlayerReputationHistory`
- Update `GamePlayer.current_reputation`
- Track headline results in `HeadlineVote`

---

## 🧪 **Testing Plan**

### **Test Scenarios**
1. **Reputation Tracking**
   - Player votes correctly → +1 RP
   - Player votes incorrectly → -1 RP
   - Player reaches 0 RP → becomes Ghost Viewer
   - Scammer gets bonus when majority wrong

2. **Win Conditions**
   - 3 fake headlines trusted → Scammers win
   - 3 fake headlines flagged → Truth team wins
   - 5 rounds completed → Truth team wins

3. **Ghost Viewer Mechanics**
   - 0 RP player cannot vote
   - 0 RP player cannot use abilities
   - 0 RP player can still receive messages

---

## 📝 **Implementation Order**

### **Phase 1: Reputation System Foundation**
1. Add RP tracking to game session initialization
2. Implement RP calculation methods
3. Add Ghost Viewer enforcement checks

### **Phase 2: Headline Win Conditions**
4. Add headline tracking to game session
5. Update vote resolution with headline counting
6. Replace win condition logic

### **Phase 3: Integration & Polish**
7. Update UI to show RP and progress
8. Add comprehensive logging
9. Test all scenarios

### **Phase 4: Verification**
10. Test complete game flows
11. Verify database logging
12. Confirm all design document requirements met

---

## ✅ **Success Criteria**

- [x] Players start with 3 RP ✅ **COMPLETED**
- [x] RP correctly increases/decreases based on votes ✅ **COMPLETED**
- [x] Players with 0 RP become Ghost Viewers ✅ **COMPLETED**
- [x] Scammers win when 3 fake headlines trusted ✅ **COMPLETED**
- [x] Truth team wins when 3 fake headlines flagged ✅ **COMPLETED**
- [x] Truth team wins after 5 rounds ✅ **COMPLETED**
- [x] All reputation changes logged to database ✅ **COMPLETED**
- [x] Win progress displayed to players ✅ **COMPLETED**
- [x] Ghost Viewer restrictions enforced ✅ **COMPLETED**

## 🎉 **IMPLEMENTATION COMPLETED**

All core reputation system and headline-based win condition features have been successfully implemented according to the design document specifications.

This plan ensures systematic implementation of the core game mechanics while maintaining code quality and following the design document exactly. 