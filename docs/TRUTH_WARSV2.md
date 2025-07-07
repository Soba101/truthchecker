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
- No special abilities beyond persuasion

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
- During Rounds **1–4**, the **Fact Checker** may use their **one-time snipe** ability to shadow-ban one player
- If the Fact Checker snipes an innocent target, they become shadow-banned instead

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

## 🎮 **Detailed 3-Round Simulation**

### **Player Setup (7 players):**
- 😈 **Alex** – Scammer
- 😈 **Bella** – Scammer  
- ✅ **Rachel** – Truth Seeker
- 🧠 **Sam** – Fact Checker
- 🎭 **Chloe** – Influencer (vote x2)
- 🧍 **Darren** – Misinformed User
- 🧍 **Erin** – Misinformed User

---

### **🕹️ ROUND 1 – Believable But Fake Health Claim**
**📰 AI Headline:** *"Wearing wireless earbuds for more than 2 hours daily has been linked to brain cancer."*

**💬 Discussion:**
- **Alex (Scammer):** "This is definitely true. I read it on an Apple discussion forum. Radiation is real."
- **Bella (Scammer):** "I agree — there's been concern about Bluetooth for a while now."
- **Rachel (Truth Seeker):** "Actually, multiple studies have shown Bluetooth radiation is non-ionising and extremely low-risk. No cancer link."
- **Chloe (Influencer):** "But doesn't all radiation cause harm over time? I'm not fully convinced it's safe."
- **Darren (Misinformed):** "I feel dizzy when I wear mine for too long, just saying."
- **Erin (Misinformed):** "This scared me before. I stopped using AirPods at night."
- **Sam (Fact Checker):** *observing quietly*

**🗳️ Voting:**
- **✅ Trust:** Alex, Bella, Chloe (x2), Darren, Erin → **Total 6 votes**
- **🚩 Flag:** Rachel → **Total 1 vote**
- **❓ Abstain:** Sam

**→ Majority trusts the claim.**

**🔎 Fact Checker Action:**
Sam checks the claim → **FAKE**. He reveals the truth to warn others.

**📉 Reputation Changes:**
- **Rachel:** +1 RP (correctly flagged fake)
- **Alex/Bella:** -1 RP (incorrectly trusted fake)
- **Chloe/Darren/Erin:** -1 RP (incorrectly trusted fake)
- **Sam:** 0 RP (no vote)

**🎯 Outcome:** Truth Team wins Round 1. Players learn about non-ionising vs. ionising radiation.

---

### **🕹️ ROUND 2 – Real but Unbelievable Headline**
**📰 AI Headline:** *"Octopuses can taste with their arms."*

**💬 Discussion:**
- **Rachel (Truth Seeker):** "This sounds bizarre, but I've read marine biology articles — it's actually true."
- **Alex (Scammer):** "Nah, this is clickbait. Animals don't have that kind of sensory system."
- **Bella (Scammer):** "Yeah, sounds like a weird joke."
- **Chloe (Influencer):** "Taste with arms?? I don't buy it."
- **Darren (Misinformed):** "I've never heard of this — must be fake."
- **Erin (Misinformed):** "No way. Sounds like fake NatGeo."
- **Sam (Fact Checker):** *watching quietly*

**🗳️ Voting:**
- **✅ Trust:** Rachel → **Total 1 vote**
- **🚩 Flag:** Alex, Bella, Chloe (x2), Darren, Erin → **Total 6 votes**

**→ Majority flags it as fake.**

**🔎 Fact Checker Reveals:** Sam announces → **TRUE**. It's an actual scientific fact.

**📉 Reputation Changes:**
- **Rachel:** +1 RP (correctly trusted real)
- **Alex/Bella/Chloe/Darren/Erin:** -1 RP (incorrectly flagged real)
- **Sam:** 0 RP (no vote)

**🎯 Outcome:** Scammers succeed by manipulating disbelief. Truth was buried in skepticism.

---

### **🕹️ ROUND 3 – Viral Social Misinformation**
**📰 AI Headline:** *"You can renew your passport faster by using the 'secret 3AM slot' trick on ICA's website."*

**💬 Discussion:**
- **Bella (Scammer):** "I've done this. Worked for me last year — got an appointment instantly."
- **Alex (Scammer):** "Yeah, it's a hidden system trick. Everyone on Reddit knows it."
- **Rachel (Truth Seeker):** "There's no official info on this. It might have worked once, but it's not real policy."
- **Chloe (Influencer):** "I've tried it — didn't work. But people swear by it."
- **Darren (Misinformed):** "Sounds like a life hack more than a lie."
- **Erin (Misinformed):** "It was viral on TikTok. So many comments said it worked!"
- **Sam (Fact Checker):** *holding back action*

**🗳️ Voting:**
- **✅ Trust:** Bella, Alex, Darren, Erin → **Total 4 votes**
- **🚩 Flag:** Rachel, Sam → **Total 2 votes**
- **❓ Abstain:** Chloe

**→ Majority trusts the viral claim.**

**🔎 Fact Checker Reveals:** Sam announces → **FAKE**. No official policy exists.

**📉 Reputation Changes:**
- **Rachel/Sam:** +1 RP (correctly flagged fake)
- **Alex/Bella/Darren/Erin:** -1 RP (incorrectly trusted fake)
- **Chloe:** 0 RP (abstained)

**🎯 Outcome:** Truth Team wins Round 3. Players learn that virality ≠ credibility.

---

### **🏁 FINAL SIMULATION RECAP:**

| **Round** | **Headline Type** | **Outcome** | **Key Lesson** |
|-----------|------------------|-------------|----------------|
| **1** | Fake but believable | Truth Team wins | Not all "scientific" claims are true |
| **2** | True but unbelievable | Scammers manipulate group | Weird ≠ Fake — biology facts can sound unreal |
| **3** | Viral myth | Truth Team wins | Virality ≠ Credibility |

**🎓 Educational Impact:**
- Players experienced how **confirmation bias** affects judgment
- Learned to distinguish between **believable lies** and **unbelievable truths**
- Understood how **social proof** (viral content) can mislead
- Practiced **source verification** and **critical thinking**

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

---

## 🚨 **Game Design Analysis: Potential Loopholes & Issues**

### **⚠️ Critical Issues Identified**

#### **1. Reputation System Vulnerabilities**
**Issue**: Everyone could become Ghost Viewers (0 RP)
- If most players make wrong votes early, they lose voting power
- Game becomes unplayable with no active voters
- **Solution**: Implement minimum 1 RP floor or reputation recovery mechanics

**Issue**: No protection against reputation manipulation
- Scammers get +1 RP when majority is wrong, creating unfair advantage
- **Solution**: Cap bonus RP or make it conditional on Scammer participation

#### **2. Role Balance Problems**
**Issue**: Fact Checker overpowered
- Knows correct answer 4 out of 5 rounds
- Can easily dominate game with perfect information
- **Solution**: Reduce to 3 out of 5 rounds or add misinformation risk

**Issue**: Influencer 2x vote too powerful in small groups
- In 5-6 player games, Influencer controls 2/5 or 2/6 of total votes
- Can single-handedly decide outcomes
- **Solution**: Scale vote weight by group size (1.5x in small groups)

**Issue**: "Drunk" role rotation breaks with insufficient normies
- Simulation shows no normies available for rotation
- Role becomes meaningless or causes errors
- **Solution**: Allow any non-special role to be "drunk" or remove rotation

#### **3. Win Condition Logic Flaws**
**Issue**: Win conditions assume balanced headline distribution
- "3 fake headlines trusted/flagged" assumes 3+ fake headlines exist
- Random generation might create 4 real, 1 fake scenario
- **Solution**: Guarantee balanced headline distribution (2-3 fake, 2-3 real)

**Issue**: Truth Team heavily favored
- Default win after 5 rounds regardless of performance
- RP-based victory calculation as tiebreaker also favors Truth Team
- **Solution**: More balanced endgame conditions

**Issue**: Unclear tie-breaking in voting
- What happens if Trust and Flag votes are equal?
- **Solution**: Define clear tie-breaking rules (abstains, coin flip, etc.)

#### **4. Shadow Ban System Inconsistencies**
**Issue**: Shadow banned players can still vote
- Punishment doesn't match severity of being "eliminated"
- Players might prefer shadow ban over active participation
- **Solution**: Remove voting rights for shadow banned players

**Issue**: Snipe timing creates unfair gaps
- Only available rounds 2 and 4, not 1, 3, 5
- Critical late-game sniping impossible
- **Solution**: Allow sniping in rounds 2, 3, 4 or 2, 4, 5

#### **5. Information Asymmetry Exploitation**
**Issue**: Scammers could reveal roles to break game
- No mechanism prevents "I'm the Scammer" declarations
- Could chaos-strategy by revealing all roles
- **Solution**: Add in-game penalties for role revelation

**Issue**: Fact Checker has no misdirection protection
- Always acts in Truth Team's favor, easily identifiable
- **Solution**: Occasionally give Fact Checker wrong information

#### **6. Player Behavior Manipulation**
**Issue**: Silent players face no consequences
- "Silence is suspicious" but no enforcement mechanism
- Players could game by staying quiet
- **Solution**: Force participation through voting penalties

**Issue**: Abstaining has no cost
- Simulation shows abstaining gives 0 RP change
- Could be exploited to avoid all risk
- **Solution**: Add small penalty for abstaining

#### **7. Voting System Exploits**
**Issue**: Vote weight imbalance
- Influencer + regular player can overpower multiple opponents
- Mathematical advantage too strong
- **Solution**: Implement diminishing returns on vote weight

**Issue**: No anti-coalition mechanics
- Players could pre-agree on voting patterns
- **Solution**: Add uncertainty elements or role swapping

### **🔧 Recommended Fixes**

#### **High Priority:**
1. **Reputation Floor**: Minimum 1 RP to prevent Ghost Viewer deadlock
2. **Role Balance**: Reduce Fact Checker advantage, scale Influencer power
3. **Win Condition Guarantee**: Ensure balanced headline distribution
4. **Shadow Ban Consistency**: Remove voting rights for shadow banned players

#### **Medium Priority:**
5. **Tie-Breaking Rules**: Define clear voting tie resolution
6. **Participation Enforcement**: Penalize silence and abstaining
7. **Anti-Reveal Mechanics**: Discourage role revelation

#### **Low Priority:**
8. **Coalition Prevention**: Add uncertainty to reduce pre-gaming
9. **Late-Game Balance**: Allow more strategic timing for abilities

### **🎯 Game Flow Improvements**

**Issue**: Phase transitions unclear
- Players may not understand when to act
- **Solution**: Clear phase indicators and countdown timers

**Issue**: Learning curve too steep
- Complex role interactions hard to grasp quickly
- **Solution**: Simplified tutorial mode or role cards

**Issue**: Endgame feels rushed
- No climactic final round mechanics
- **Solution**: Add final round special rules or reveal mechanics

---

## 🔍 **Conclusion**

The Truth Wars game design has strong educational value and engaging mechanics, but contains several exploitable loopholes that could break gameplay. The most critical issues are:

1. **Reputation system** could eliminate all players from voting
2. **Role balance** heavily favors informed players
3. **Win conditions** don't guarantee achievable objectives
4. **Shadow ban system** lacks consistency

Addressing these issues would create a more balanced, fair, and engaging experience while maintaining the core educational objectives.