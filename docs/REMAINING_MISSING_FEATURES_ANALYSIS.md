# 📋 Remaining Missing Features Analysis

## 🎯 **Overview**
After implementing the reputation system and headline-based win conditions, this document identifies the remaining features missing from the Truth Wars implementation compared to the design document.

---

## 🚨 **CRITICAL MISSING FEATURES**

### **1. 🎭 Influencer Double Vote Weight**
**Status:** ✅ **COMPLETED**

**Current State:**
- ✅ Database models have vote weight fields
- ✅ Influencer role has `get_vote_weight()` method returning 2
- ❌ Vote resolution uses simple counting: `trust_votes = len(trust_voters)`

**Required Fix:**
```python
# In _resolve_voting() - Replace simple counting with weighted counting
weighted_trust_votes = 0
weighted_flag_votes = 0

for voter_id in trust_voters:
    role_info = game_session["player_roles"].get(voter_id, {})
    role = role_info.get("role")
    vote_weight = role.get_vote_weight() if role else 1
    weighted_trust_votes += vote_weight

for voter_id in flag_voters:
    role_info = game_session["player_roles"].get(voter_id, {})
    role = role_info.get("role")
    vote_weight = role.get_vote_weight() if role else 1
    weighted_flag_votes += vote_weight

majority_trusts = weighted_trust_votes > weighted_flag_votes
```

**Impact:** HIGH - Core game mechanic for Influencer role

---

### **2. 🧍 Drunk Role Rotation**
**Status:** ✅ **COMPLETED**

**Current State:**
- Drunk role assigned once at game start
- Design requires: "Rotates among normies each round"

**Required Implementation:**
```python
async def _rotate_drunk_role(self, game_session: Dict) -> None:
    """Rotate the Drunk role to a different normie each round."""
    # Find all normies (not FactChecker, Scammer, or Influencer)
    normies = []
    for player_id, role_info in game_session["player_roles"].items():
        role = role_info.get("role")
        if role and role.__class__.__name__ == "Normie":
            normies.append(player_id)
    
    # Rotate to next normie
    current_round = game_session["round_number"]
    if normies:
        new_drunk_index = (current_round - 1) % len(normies)
        new_drunk_id = normies[new_drunk_index]
        
        # Update role assignments
        # Remove old drunk, assign new drunk
```

**Impact:** HIGH - Core role mechanic

---

### **3. 🧠 Fact Checker "No Info Round"**
**Status:** ✅ **COMPLETED**

**Current State:**
- Fact Checker always receives correct answer
- Design requires: "Receives correct answer every round **except one**"

**Required Implementation:**
```python
# In game session initialization
game_session["fact_checker_no_info_round"] = random.randint(1, 5)

# In _start_news_phase()
current_round = game_session["round_number"]
no_info_round = game_session["fact_checker_no_info_round"]

for player_id, role_info in game_session["player_roles"].items():
    role = role_info.get("role")
    if role.__class__.__name__ == "FactChecker":
        if current_round != no_info_round:
            # Send correct answer
        else:
            # Send "no info this round" message
```

**Impact:** MEDIUM - Balances Fact Checker power

---

### **4. ⏰ Discussion Timer Inconsistency**
**Status:** ✅ **COMPLETED**

**Current State:**
- Design document: 3 minutes (180 seconds)
- `refined_game_states.py`: 180 seconds ✅
- `game_states.py`: 300 seconds ❌

**Required Fix:**
- Standardize all timing to 180 seconds (3 minutes)
- Ensure consistent enforcement across all game state files

**Impact:** MEDIUM - Game balance and design consistency

---

## 📝 **IMPORTANT MISSING FEATURES**

### **5. 🎯 Snipe Timing Restriction**
**Status:** ❌ **NOT IMPLEMENTED**

**Design Requirement:** "Every 2 rounds, eligible roles can use their snipe ability"

**Current State:** No timing restrictions on snipe usage

**Required Implementation:**
```python
def _can_use_snipe_this_round(self, game_session: Dict, player_id: int) -> bool:
    """Check if player can use snipe ability this round."""
    current_round = game_session["round_number"]
    # Allow snipes on rounds 2, 4 (every 2 rounds)
    return current_round % 2 == 0 and current_round <= 4
```

**Impact:** MEDIUM - Balances snipe abilities

---

### **6. 📚 Educational Content Integration**
**Status:** ❌ **NOT IMPLEMENTED**

**Design Requirements:**
- Drunk player should share "source verification tips"
- Educational messaging about media literacy
- Learning elements integrated into gameplay

**Required Implementation:**
- Add educational content database/messages
- Drunk role automatically shares tips each round
- Post-game educational summaries

**Impact:** MEDIUM - Core educational goal of game

---

### **7. 🔔 Enhanced Shadow Ban Messaging**
**Status:** ⚠️ **PARTIALLY IMPLEMENTED**

**Current State:**
- Basic shadow ban system exists
- Missing proper announcements

**Design Requirement:** 
- Bot announces: *"[Player] gets banned this round - no talking"*
- Strategic confusion messaging

**Impact:** LOW - UX improvement

---

## 🎨 **ENHANCEMENT FEATURES**

### **8. 📊 Real-time RP Display**
**Status:** ❌ **NOT IMPLEMENTED**

**Requirement:** Show RP changes immediately after each vote

**Implementation:**
- Display reputation changes in headline resolution
- Show current RP status in game progress messages

**Impact:** LOW - UX improvement

---

### **9. 🔍 Enhanced Vote Weight Logging**
**Status:** ❌ **NOT IMPLEMENTED**

**Requirement:** Proper database logging of weighted votes

**Current State:** Database models exist but not fully utilized

**Impact:** LOW - Data tracking and analysis

---

## 📋 **IMPLEMENTATION PRIORITY**

### **Phase 1: Critical Game Mechanics**
1. **Influencer Double Vote Weight** - Fix vote resolution logic
2. **Drunk Role Rotation** - Implement round-by-round rotation
3. **Fact Checker No Info Round** - Add one round without info

### **Phase 2: Balance & Consistency**
4. **Discussion Timer Standardization** - Fix 3-minute consistency
5. **Snipe Timing Restriction** - Every 2 rounds rule

### **Phase 3: Educational & UX**
6. **Educational Content** - Source verification tips
7. **Enhanced Messaging** - Shadow ban announcements
8. **Real-time RP Display** - Immediate feedback

---

## ✅ **SUCCESS CRITERIA**

After implementing these features, the game should:

- [x] ✅ **Reputation System** - Complete with Ghost Viewers
- [x] ✅ **Headline Win Conditions** - 3 fake headlines trusted/flagged
- [x] ✅ **Influencer Vote Weight** - 2x vote power implemented
- [x] ✅ **Drunk Role Rotation** - Changes each round among normies
- [x] ✅ **Fact Checker Balance** - One round without info
- [x] ✅ **3-Minute Discussions** - Consistent timing
- [ ] ❌ **Snipe Timing** - Every 2 rounds restriction
- [ ] ❌ **Educational Content** - Source verification integrated

---

## 🎯 **Next Steps**

1. **Start with Phase 1** - Critical game mechanics
2. **Test each feature** thoroughly before moving to next
3. **Verify design document compliance** after each implementation
4. **Update this document** as features are completed

This analysis ensures we systematically complete the Truth Wars implementation to match the refined design document exactly. 