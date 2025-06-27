# 🚀 Truth Wars Refined Implementation Roadmap

## 🎯 **Overview**
This document outlines the complete transformation needed to implement the refined Truth Wars game design. This is a **major redesign** from the current system.

## 📊 **Current vs Refined System Comparison**

| Aspect | Current System | Refined System |
|--------|----------------|----------------|
| **Game Goal** | Eliminate opposing faction | Vote accurately on headlines |
| **Voting System** | Vote to eliminate players | Vote Trust/Flag on headlines |
| **Player Status** | Alive/Dead | Reputation Points (3 RP → 0 RP) |
| **Elimination** | Traditional elimination | Shadow ban system |
| **Game Length** | Variable rounds until elimination | Fixed 5 rounds |
| **Roles** | 6 complex roles with abilities | 5 streamlined roles with snipe |
| **Win Conditions** | Faction elimination | 3 headlines voted correctly |

## 🔧 **Major Code Changes Required**

### 1. **Role System Overhaul** ✅ *COMPLETED*
**File:** `bot/game/roles.py`

**Changes Made:**
- ✅ New role definitions: Fact Checker, Scammer, Drunk, Influencer, Normie
- ✅ Snipe ability system instead of complex role abilities
- ✅ Proper role assignment for 5-6 players vs 7+ players
- ✅ Faction alignment: mostly Truth Seekers vs few Scammers

### 2. **Game State Machine Redesign** 🔄 *NEEDS UPDATE*
**File:** `bot/game/game_states.py` → Create new `refined_game_states.py`

**Required Changes:**
- [ ] New phase structure: Lobby → Role Assignment → Headline Reveal → Discussion → Voting → Results → (Snipe) → Next Round
- [ ] 5-round limit with proper transition logic
- [ ] Trust/Flag voting handling
- [ ] Shadow ban enforcement during phases
- [ ] Snipe opportunity phases (rounds 2 & 4)
- [ ] Win condition checking after each round

### 3. **Truth Wars Manager Transformation** 🔄 *NEEDS MAJOR UPDATE*
**File:** `bot/game/truth_wars_manager.py`

**Required Changes:**
- [ ] **Reputation System**: Track 3 RP per player, Ghost Viewer at 0 RP
- [ ] **Trust/Flag Voting**: Replace elimination voting with headline voting
- [ ] **Shadow Ban System**: Replace elimination with temporary communication ban
- [ ] **Drunk Role Rotation**: Assign "Drunk" role to different normie each round
- [ ] **Vote Weight System**: Handle Influencer's 2x vote weight
- [ ] **Win Condition Tracking**: Count fake headlines trusted/flagged (3 = win)
- [ ] **Snipe Mechanics**: Handle shadow ban abilities every 2 rounds

### 4. **Database Model Updates** 🔄 *NEEDS NEW MODELS*
**File:** `bot/database/models.py`

**Required Changes:**
- [ ] **Player Reputation Table**: Track RP changes over time
- [ ] **Headline Votes Table**: Record Trust/Flag votes per round
- [ ] **Shadow Ban Table**: Track shadow ban status and duration
- [ ] **Round Results Table**: Store outcome of each round (real/fake, majority vote)
- [ ] **Snipe Actions Table**: Log snipe attempts and results

### 5. **Handler Logic Updates** 🔄 *NEEDS SIGNIFICANT CHANGES*
**Files:** `bot/handlers/truth_wars_handlers.py`, `bot/handlers/message_handlers.py`

**Required Changes:**
- [ ] **Trust/Flag Vote Buttons**: Replace elimination voting UI
- [ ] **Reputation Display**: Show RP in player status
- [ ] **Shadow Ban Enforcement**: Prevent shadow banned players from talking
- [ ] **Snipe Command Handling**: /snipe command for eligible roles
- [ ] **Round Progress Display**: Show round X/5, win condition progress
- [ ] **Phase-Specific Messages**: Different messages for each phase

### 6. **New Game Features** 🆕 *NEW IMPLEMENTATIONS*

#### **Reputation System**
- [ ] Start all players with 3 RP
- [ ] +1 RP for correct votes
- [ ] -1 RP for incorrect votes
- [ ] +1 RP for Scammers when majority votes incorrectly
- [ ] Ghost Viewer status at 0 RP (can watch, can't vote/talk)

#### **Shadow Ban System**
- [ ] Prevent communication during Discussion phase
- [ ] Allow voting during Voting phase
- [ ] Clear notification to group when someone is shadow banned
- [ ] Strategic confusion (players don't know if banned player was Scammer/Fact Checker)

#### **Trust/Flag Voting**
- [ ] Clear voting interface with Trust/Flag buttons
- [ ] Vote weight handling (Influencer = 2x)
- [ ] Public vote results display
- [ ] Immediate RP updates after results

#### **Drunk Role Rotation**
- [ ] Randomly assign "Drunk" status to a different normie each round
- [ ] Send headline truth to current "Drunk" player
- [ ] Encourage sharing of media literacy tips

## 📋 **Implementation Priority**

### **Phase 1: Core Game Logic** 🎯
1. ✅ Update role system (`roles.py`) 
2. [ ] Create refined state machine (`refined_game_states.py`)
3. [ ] Update truth wars manager with reputation system
4. [ ] Add basic Trust/Flag voting

### **Phase 2: Database & Persistence** 💾
1. [ ] Add reputation tracking models
2. [ ] Add headline voting models
3. [ ] Add shadow ban tracking
4. [ ] Migrate existing games (if needed)

### **Phase 3: User Interface** 🎮
1. [ ] Update voting buttons (Trust/Flag)
2. [ ] Add reputation display
3. [ ] Update phase messages
4. [ ] Add snipe command interface

### **Phase 4: Advanced Features** ⭐
1. [ ] Shadow ban enforcement
2. [ ] Drunk role rotation
3. [ ] Snipe mechanics
4. [ ] Win condition checking

### **Phase 5: Polish & Testing** ✨
1. [ ] Message formatting improvements
2. [ ] Error handling
3. [ ] Game balance testing
4. [ ] Educational content integration

## 🧪 **Testing Strategy**

### **Unit Tests Needed:**
- [ ] Role assignment logic (5-6 vs 7+ players)
- [ ] Reputation calculation
- [ ] Vote weight calculation (Influencer)
- [ ] Win condition detection
- [ ] Phase transition logic

### **Integration Tests Needed:**
- [ ] Full 5-round game simulation
- [ ] Snipe ability testing
- [ ] Shadow ban enforcement
- [ ] Multi-player voting scenarios

### **Manual Testing Scenarios:**
- [ ] 5-player game (minimum setup)
- [ ] 7+ player game (with Influencer)
- [ ] Scammer win scenario (3 fakes trusted)
- [ ] Truth team win scenario (3 fakes flagged)
- [ ] Shadow ban scenarios

## 📚 **Educational Content**

### **Headlines Database** 📰
- [ ] Create/expand headline database with real/fake news
- [ ] Add source credibility information
- [ ] Add explanation for each headline
- [ ] Category and difficulty tagging

### **Media Literacy Tips** 🧠
- [ ] Source verification techniques
- [ ] Red flag identification
- [ ] Fact-checking resources
- [ ] Critical thinking prompts

## 🎯 **Success Metrics**

### **Gameplay Metrics:**
- ✅ Game completion rate
- ✅ Player engagement (rounds participated)
- ✅ Voting accuracy improvement over time
- ✅ Role balance (win rates by faction)

### **Educational Metrics:**
- ✅ Media literacy skill improvement
- ✅ Player feedback on learning value
- ✅ Real-world application of skills learned

## 🚀 **Next Steps**

1. **Continue with Phase 1**: Update game state machine and truth wars manager
2. **Create test scenarios**: Set up unit tests for new role system
3. **Plan database migration**: Design new schema for reputation system
4. **Update handlers**: Modify bot commands for new game flow

---

This refined system will create a **much more educational and engaging** experience that truly teaches media literacy skills while maintaining the fun social deduction elements! 🎓✨ 