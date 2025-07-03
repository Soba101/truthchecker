# 🕵️‍♂️ Truth Wars: Refined Game Design 🕵️‍♀️

## 🎯 **Game Overview**
Truth Wars is a **media literacy social deduction game** where players evaluate headlines and build reputation while special roles attempt to manipulate the outcome.

## 👥 **Player Roles & Setup**

### **5-6 Players**
- **🧠 1x Fact Checker** - Truth Seeker with investigation power
- **😈 1x Scammer** - Misinformer trying to manipulate votes  
- **🧍 1x "Drunk"** - Rotating role that gets inside info each round
- **🧍 2-3x Misinformed Users** - Regular players ("normies")

### **7+ Players** 
- **🧠 1x Fact Checker** - Truth Seeker with investigation power
- **😈 2x Scammers** - Multiple misinformers working together
- **🎭 1x Influencer** - Special role with double vote weight
- **🧍 1x "Drunk"** - Rotating role that gets inside info each round  
- **🧍 3+x Misinformed Users** - Regular players ("normies")

## 🎮 **Game Mechanics**

### **🌟 Reputation System**
- All players start with **3 Reputation Points (RP)**
- Gain/lose RP based on voting accuracy and game events
- Players with **0 RP** become "Ghost Viewers" (watch only, can't vote)

### **📰 Round Structure (5 Rounds Total)**

#### **1. AI Headline Drop**
AI generates a headline (real or fake):
- *"Eating eggs daily increases the risk of memory loss, new study says."*
- *"Octopuses can taste with their arms."* (true)
- *"Wearing wireless earbuds for more than 2 hours daily linked to brain cancer."*
- *"A Harvard study found alkaline water drinkers are 40% less likely to get cancer."*

#### **2. Discussion Phase (3 minutes)**
- All players debate the headline's authenticity
- **Scammers** try to create doubt or push false certainty
- **Truth Seekers** guide debate subtly  
- **Silence is suspicious** - all must participate

#### **3. Trust/Flag Vote**
- Players vote: **TRUST** (believe it's real) or **FLAG** (think it's fake)
- **Influencer** vote counts as 2 votes
- Public voting results displayed

#### **4. Reputation Updates**
**Correct Votes:**
- Supporting true headlines → **+1 RP**
- Flagging fake headlines → **+1 RP**

**Incorrect Votes:**
- Voting TRUST on fake headline → **-1 RP**
- Voting FLAG on true headline → **-1 RP**

**Special Bonus:**
- If majority gets wrong option → **Scammers get +1 RP**

## 🎭 **Special Role Abilities**

### **🧠 Fact Checker**
- Receives correct answer every round **except one**
- **One-time "snipe" ability** per game to shadow ban suspected Scammer
- **Risk**: If they snipe wrong person, they get shadow banned instead
- Must be subtle to avoid being targeted by Scammers

### **😈 Scammer(s)**
- Know which headlines are real/fake
- Goal: Manipulate others into wrong votes
- **One-time "snipe" ability** per game to shadow ban suspected Fact Checker
- **Risk**: If they snipe wrong person, they get shadow banned instead

### **🧍 "Drunk" Role**
- **Rotates among normies each round**
- Receives the correct answer for that round's headline
- Must share information with everyone
- **Learning opportunity**: Explains how to identify reliable sources

### **🎭 Influencer** (7+ players only)
- **Vote weight x2** - their vote counts double
- Regular player otherwise, but with increased influence

## 🚫 **Shadow Ban System**

### **When It Happens**
- Every 2 rounds, eligible roles can use their "snipe" ability
- Failed snipe attempts result in self-shadow ban

### **Shadow Ban Effects**
- Banned player cannot talk during discussion phase
- Bot announces: *"[Player] gets banned this round - no talking"*
- **Strategic confusion**: Other players don't know if banned player was Scammer or Fact Checker
- Shadow banned players can still vote

## 🏆 **Win Conditions**

### **🔥 Scammers Win If:**
- **3 fake headlines are trusted** by majority vote
- All Truth Seekers are shadow banned or eliminated

### **✅ Truth Team Wins If:**
- **3 fake headlines are flagged correctly** by majority vote  
- All Scammers are shadow banned or eliminated
- Game reaches 5 rounds without Scammer victory

### **🎮 Game Ends When:**
- Win condition is met, OR
- 5 rounds completed (Truth Team wins by default)

## 📊 **Example Round Flow**

### **Round 1**
1. **Headline**: *"Drinking alkaline water reduces cancer risk by 40%"* (FAKE)
2. **Discussion**: Players debate for 3 minutes
   - Fact Checker knows it's fake (subtly guides discussion)
   - Scammer tries to convince people it's real
   - "Drunk" player shares source verification tips
3. **Vote**: TRUST: 3 players, FLAG: 2 players
4. **Result**: Headline was FAKE
   - TRUST voters: -1 RP each
   - FLAG voters: +1 RP each  
   - Scammers: +1 RP (majority was wrong)

## 🎯 **Strategic Elements**

### **For Truth Seekers:**
- **Fact Checker**: Share knowledge subtly without revealing role
- **Normies**: Learn to identify reliable sources and logical arguments
- **Influencer**: Use double vote strategically

### **For Scammers:**
- Blend in with Truth Seekers
- Create convincing false arguments
- Target Fact Checker with snipe ability
- Manipulate group psychology

### **For Everyone:**
- **Reputation management**: Avoid hitting 0 RP
- **Social deduction**: Identify who's misleading the group
- **Media literacy**: Actually learn to spot fake news

## 🧠 **Educational Value**

- **Source evaluation**: Learn to check credibility
- **Critical thinking**: Analyze claims and evidence
- **Psychology awareness**: Understand manipulation tactics
- **Real skills**: Apply lessons to actual news consumption

## 🔧 **Technical Implementation Notes**

- **Automated headline generation**: Mix of real and fake news
- **Reputation tracking**: Persistent across rounds
- **Role rotation**: "Drunk" role changes each round
- **Timer system**: Enforced 3-minute discussion phases
- **Vote weighting**: Handle Influencer's 2x vote power
- **Shadow ban system**: Restrict communication abilities