# 🚀 Truth Wars: Missing Features Implementation Plan

## 📋 **Executive Summary**

This document outlines the implementation plan for missing features from the `TRUTH_WARS_REFINED_GAME_DESIGN.md` specification. The features are prioritized by impact and complexity, with detailed technical specifications for each.

**Current Status:** 85% of core features implemented
**Missing Critical Features:** 4 high-priority, 3 medium-priority
**Estimated Implementation Time:** 2-3 weeks

---

## 🎯 **HIGH PRIORITY FEATURES**

### **1. 🎯 Snipe Timing Restriction System**

**Status:** ❌ **NOT IMPLEMENTED**  
**Priority:** HIGH  
**Complexity:** LOW  
**Estimated Time:** 2-4 hours

#### **Design Requirement**
- Snipe abilities only available on rounds 2 and 4 (every 2 rounds)
- Clear messaging when snipes are/aren't available
- Proper phase transitions for snipe opportunities

#### **Technical Specification**

**Files to Modify:**
- `bot/game/truth_wars_manager.py`
- `bot/game/refined_game_states.py`
- `bot/handlers/truth_wars_handlers.py`

**Implementation Steps:**

1. **Add snipe timing validation to Truth Wars Manager:**

```python
# In bot/game/truth_wars_manager.py

def _can_use_snipe_this_round(self, game_session: Dict, player_id: int) -> bool:
    """Check if player can use snipe ability this round."""
    current_round = game_session["round_number"]
    
    # Snipes only available on rounds 2 and 4
    snipe_rounds = [2, 4]
    
    if current_round not in snipe_rounds:
        return False
    
    # Check if player has snipe ability and hasn't used it
    role_info = game_session["player_roles"].get(player_id)
    if not role_info:
        return False
        
    role = role_info.get("role")
    return role and role.can_use_snipe()

def _is_snipe_round(self, round_number: int) -> bool:
    """Check if current round allows snipe abilities."""
    return round_number in [2, 4]
```

2. **Update phase transition logic:**

```python
# In bot/game/refined_game_states.py

elif self.current_phase == PhaseType.ROUND_RESULTS:
    # Check if this is a snipe round
    if self._is_snipe_round(self.round_number):
        self.current_phase = PhaseType.SNIPE_OPPORTUNITY
    else:
        # Move to next round or end game
        if self._should_end_game(game_state):
            self.current_phase = PhaseType.GAME_END
        elif self.round_number < self.max_rounds:
            self.round_number += 1
            self.current_phase = PhaseType.HEADLINE_REVEAL
        else:
            self.current_phase = PhaseType.GAME_END

def _is_snipe_round(self, round_number: int) -> bool:
    """Check if round allows snipe abilities."""
    return round_number in [2, 4]
```

3. **Add snipe availability messaging:**

```python
# Add to phase transition messages
if new_phase == "snipe_opportunity":
    snipe_message = (
        f"🎯 **Round {game_session['round_number']}: Snipe Opportunity!**\n\n"
        f"⚡ **Fact Checkers** and **Scammers** can now use their snipe abilities!\n"
        f"🎯 Target your suspected enemies to shadow ban them\n"
        f"⚠️ **WARNING**: Wrong target = YOU get shadow banned!\n\n"
        f"⏰ **90 seconds** to decide..."
    )
```

**Testing Checklist:**
- [ ] Snipe abilities blocked on rounds 1, 3, 5
- [ ] Snipe abilities available on rounds 2, 4
- [ ] Proper error messages when snipe unavailable
- [ ] Phase transitions work correctly

---

### **2. 📚 Educational Content Delivery System**

**Status:** ❌ **NOT IMPLEMENTED**  
**Priority:** HIGH  
**Complexity:** MEDIUM  
**Estimated Time:** 6-8 hours

#### **Design Requirement**
- Drunk player automatically shares source verification tips
- Educational messaging integrated into gameplay
- Learning elements that improve media literacy

#### **Technical Specification**

**Files to Modify:**
- `bot/game/truth_wars_manager.py`
- `bot/database/seed_data.py`
- `bot/handlers/truth_wars_handlers.py`

**Implementation Steps:**

1. **Create educational content delivery system:**

```python
# In bot/game/truth_wars_manager.py

async def _send_educational_content_to_drunk(self, game_session: Dict) -> None:
    """Send educational content to current drunk player."""
    try:
        from ..database.seed_data import get_media_literacy_tip
        
        drunk_rotation = game_session["drunk_rotation"]
        current_drunk_id = drunk_rotation.get("current_drunk_id")
        
        if not current_drunk_id:
            return
            
        # Get appropriate educational tip
        current_headline = game_session.get("current_headline")
        headline_category = current_headline.get("category", "general") if current_headline else "general"
        
        educational_tip = await get_media_literacy_tip(category=headline_category)
        
        bot_context = getattr(self, '_bot_context', None)
        if not bot_context:
            return
            
        tip_message = (
            f"📚 **DRUNK EDUCATIONAL CONTENT**\n\n"
            f"🎯 **Your Teaching Mission:**\n"
            f"During discussion, share this tip with everyone:\n\n"
            f"💡 **{educational_tip['title']}**\n"
            f"{educational_tip['content']}\n\n"
            f"🔍 **Example:** {educational_tip['example']}\n\n"
            f"📢 **Share this during discussion to help others learn!**"
        )
        
        await bot_context.bot.send_message(
            chat_id=current_drunk_id,
            text=tip_message
        )
        
        # Track educational content delivered
        game_session.setdefault("educational_content_delivered", []).append({
            "round": game_session["round_number"],
            "drunk_player": current_drunk_id,
            "tip_category": educational_tip["category"],
            "tip_id": educational_tip.get("id")
        })
        
        logger.info(f"Educational content sent to drunk player {current_drunk_id}")
        
    except Exception as e:
        logger.error(f"Failed to send educational content to drunk: {e}")

async def _remind_drunk_to_teach(self, game_session: Dict) -> None:
    """Remind drunk player to share educational content during discussion."""
    drunk_rotation = game_session["drunk_rotation"]
    current_drunk_id = drunk_rotation.get("current_drunk_id")
    
    if not current_drunk_id:
        return
        
    bot_context = getattr(self, '_bot_context', None)
    if not bot_context:
        return
        
    reminder_message = (
        f"📢 **REMINDER: Share Your Educational Tip!**\n\n"
        f"Don't forget to share the media literacy tip I gave you during the discussion phase. "
        f"Help your fellow players learn how to spot fake news! 🧠✨"
    )
    
    await bot_context.bot.send_message(
        chat_id=current_drunk_id,
        text=reminder_message
    )
```

2. **Enhance media literacy tip system:**

```python
# In bot/database/seed_data.py

ENHANCED_MEDIA_LITERACY_TIPS = [
    {
        "id": "source_check_1",
        "category": "source_verification",
        "title": "Check the Source's Reputation",
        "content": "Always look at WHO published the article. Reputable news sources have editorial standards and fact-checking processes.",
        "example": "BBC, Reuters, AP News = trusted. Random blog or social media post = be skeptical!",
        "detection_keywords": ["source", "author", "publication"],
        "application": "Look at the URL and publication name before believing any headline."
    },
    {
        "id": "date_check_1", 
        "category": "context_verification",
        "title": "Check Publication Dates",
        "content": "Old news can be recycled to seem current. Always check when an article was actually published.",
        "example": "A 2019 study about vaccines being shared in 2024 without date context can mislead people.",
        "detection_keywords": ["date", "when", "published"],
        "application": "Always look for publication dates, especially on social media shares."
    },
    {
        "id": "emotional_1",
        "category": "emotional_manipulation", 
        "title": "Recognize Emotional Language",
        "content": "Fake news often uses extreme emotional language to bypass critical thinking. Words like 'SHOCKING', 'UNBELIEVABLE', 'DOCTORS HATE THIS' are red flags.",
        "example": "'You WON'T BELIEVE what this miracle cure does!' vs 'Clinical trial shows promising results for new treatment'",
        "detection_keywords": ["shocking", "unbelievable", "amazing", "hate"],
        "application": "Be extra skeptical of headlines that seem designed to make you angry or excited."
    }
    # ... add more tips
]

async def get_contextual_media_literacy_tip(headline_text: str, category: str = None) -> Dict[str, Any]:
    """Get media literacy tip relevant to current headline."""
    import random
    
    # Analyze headline for relevant tip
    headline_lower = headline_text.lower()
    
    relevant_tips = []
    for tip in ENHANCED_MEDIA_LITERACY_TIPS:
        # Check if tip keywords appear in headline
        for keyword in tip["detection_keywords"]:
            if keyword in headline_lower:
                relevant_tips.append(tip)
                break
    
    # Fallback to category-based selection
    if not relevant_tips and category:
        relevant_tips = [tip for tip in ENHANCED_MEDIA_LITERACY_TIPS if tip["category"] == category]
    
    # Final fallback to random tip
    if not relevant_tips:
        relevant_tips = ENHANCED_MEDIA_LITERACY_TIPS
    
    return random.choice(relevant_tips)
```

3. **Integrate into game flow:**

```python
# Update _start_news_phase to include educational content
async def _start_news_phase(self, game_session: Dict) -> None:
    """Start a new news phase with headline and educational content."""
    # ... existing code ...
    
    # Send educational content to drunk player
    await self._send_educational_content_to_drunk(game_session)
    
    # ... rest of existing code ...

# Add reminder during discussion phase
async def _handle_phase_transition(self, game_session: Dict, transition_result: Dict) -> None:
    """Handle phase transition by sending appropriate messages to chat."""
    # ... existing code ...
    
    if new_phase == "discussion":
        # Send voting buttons for headline during discussion phase
        current_headline = game_session.get("current_headline")
        if current_headline:
            await send_headline_voting(bot_context, game_session["chat_id"], current_headline)
        
        # Remind drunk to share educational tip
        await self._remind_drunk_to_teach(game_session)
```

**Testing Checklist:**
- [ ] Drunk receives educational content each round
- [ ] Tips are contextually relevant to headlines
- [ ] Reminder messages sent during discussion
- [ ] Educational content tracked in database

---

### **3. 🤖 AI Headline Generation System**

**Status:** ❌ **NOT IMPLEMENTED**  
**Priority:** MEDIUM  
**Complexity:** HIGH  
**Estimated Time:** 8-12 hours

#### **Design Requirement**
- AI generates realistic fake and real headlines
- Dynamic content instead of pre-seeded only
- Appropriate difficulty scaling

#### **Technical Specification**

**Files to Create:**
- `bot/ai/headline_generator.py`
- `bot/ai/__init__.py`

**Files to Modify:**
- `bot/game/truth_wars_manager.py`
- `requirements.txt`

**Implementation Steps:**

1. **Create AI headline generator:**

```python
# Create bot/ai/headline_generator.py

import openai
import random
from typing import Dict, List, Optional
from ..utils.config import get_settings
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class HeadlineGenerator:
    """AI-powered headline generator for Truth Wars."""
    
    def __init__(self):
        self.settings = get_settings()
        # Initialize OpenAI client or alternative AI service
        self.client = openai.OpenAI(api_key=self.settings.OPENAI_API_KEY)
        
    async def generate_headline(self, difficulty: str = "medium", category: str = "general", is_real: bool = None) -> Dict[str, any]:
        """Generate a realistic headline."""
        
        if is_real is None:
            is_real = random.choice([True, False])
            
        difficulty_prompts = {
            "easy": "obvious fake news that most people can identify",
            "medium": "moderately believable fake news that requires some critical thinking",
            "hard": "very sophisticated fake news that's difficult to distinguish from real news"
        }
        
        category_contexts = {
            "health": "health, medicine, or wellness",
            "politics": "political news or government",
            "technology": "technology, science, or innovation", 
            "general": "general news"
        }
        
        if is_real:
            prompt = f"""Generate a real, factual news headline about {category_contexts.get(category, 'general news')}. 
            The headline should be:
            - Actually true and verifiable
            - Realistic and properly formatted
            - Appropriate for a {difficulty} difficulty level
            - Not sensationalized or clickbait
            
            Return ONLY the headline text, nothing else."""
        else:
            prompt = f"""Generate a fake news headline about {category_contexts.get(category, 'general news')}. 
            The headline should be:
            - {difficulty_prompts.get(difficulty, 'moderately believable')}
            - Realistic-sounding but false
            - Designed for a media literacy education game
            - Difficulty: {difficulty}
            
            Return ONLY the headline text, nothing else."""
        
        try:
            response = await self.client.chat.completions.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.8
            )
            
            headline_text = response.choices[0].message.content.strip()
            
            # Generate explanation
            explanation = await self._generate_explanation(headline_text, is_real, difficulty)
            
            return {
                "text": headline_text,
                "is_real": is_real,
                "source": "AI Generated",
                "explanation": explanation,
                "category": category,
                "difficulty": difficulty,
                "ai_generated": True
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI headline: {e}")
            # Fallback to pre-seeded headlines
            return None
    
    async def _generate_explanation(self, headline: str, is_real: bool, difficulty: str) -> str:
        """Generate educational explanation for why headline is real/fake."""
        
        if is_real:
            prompt = f"""Explain why this headline is REAL/TRUE in 2-3 sentences. Focus on:
            - What makes it credible
            - How someone could verify it
            - Why it's realistic
            
            Headline: "{headline}"
            
            Keep explanation educational and concise."""
        else:
            prompt = f"""Explain why this headline is FAKE in 2-3 sentences. Focus on:
            - Red flags that indicate it's false
            - How someone could fact-check it
            - What makes it suspicious
            
            Headline: "{headline}"
            
            Keep explanation educational for media literacy learning."""
        
        try:
            response = await self.client.chat.completions.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return f"This headline is {'real' if is_real else 'fake'}. Use critical thinking and fact-checking to verify news sources."
```

2. **Integrate into game manager:**

```python
# In bot/game/truth_wars_manager.py

from ..ai.headline_generator import HeadlineGenerator

class TruthWarsManager:
    def __init__(self):
        # ... existing init code ...
        self.headline_generator = HeadlineGenerator()
    
    async def get_random_headline(self, difficulty: str = "medium", category: Optional[str] = None) -> Optional[Headline]:
        """Get a headline - try AI first, fallback to database."""
        
        # 50% chance to use AI-generated headline
        if random.choice([True, False]):
            try:
                ai_headline = await self.headline_generator.generate_headline(
                    difficulty=difficulty, 
                    category=category
                )
                
                if ai_headline:
                    # Create temporary headline object
                    return type('Headline', (), ai_headline)()
            except Exception as e:
                logger.warning(f"AI headline generation failed, using database: {e}")
        
        # Fallback to existing database headlines
        # ... existing database query code ...
```

3. **Add configuration:**

```python
# Add to requirements.txt
openai>=1.0.0

# Add to bot/utils/config.py
class Settings:
    # ... existing settings ...
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_HEADLINE_ENABLED: bool = os.getenv("AI_HEADLINE_ENABLED", "false").lower() == "true"
```

**Testing Checklist:**
- [ ] AI generates realistic fake headlines
- [ ] AI generates credible real headlines  
- [ ] Explanations are educational and accurate
- [ ] Fallback to database works when AI fails
- [ ] Difficulty scaling works properly

---

## 🔧 **MEDIUM PRIORITY FEATURES**

### **4. 🚫 Enhanced Shadow Ban Communication Enforcement**

**Status:** ⚠️ **PARTIALLY IMPLEMENTED**  
**Priority:** MEDIUM  
**Complexity:** MEDIUM  
**Estimated Time:** 4-6 hours

#### **Implementation Steps:**

1. **Add message filtering in handlers:**

```python
# In bot/handlers/message_handlers.py

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages in group chats with shadow ban filtering."""
    
    if not update.message or not update.effective_user:
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Check if there's an active game
    game_id = context.chat_data.get('current_game_id')
    if not game_id:
        return
    
    # Check if user is shadow banned
    from ..game.truth_wars_manager import truth_wars_manager
    game_status = await truth_wars_manager.get_game_status(game_id)
    
    if game_status and game_status.get("current_phase") == "discussion":
        # Check shadow ban status
        shadow_banned_players = game_status.get("shadow_banned_players", {})
        if user_id in shadow_banned_players and shadow_banned_players[user_id] > 0:
            # Delete the message and notify privately
            await update.message.delete()
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🚫 **You are shadow banned!**\n\nYou cannot speak during discussion phases. You can still vote on headlines."
                )
            except:
                pass  # User might have blocked the bot
            
            return
    
    # ... handle normal message processing ...
```

### **5. 📊 Real-time RP Display System**

**Implementation Steps:**

```python
# In bot/game/truth_wars_manager.py

async def _send_reputation_update(self, game_session: Dict, reputation_changes: Dict) -> None:
    """Send real-time reputation updates after voting."""
    
    bot_context = getattr(self, '_bot_context', None)
    if not bot_context:
        return
    
    # Build reputation change message
    rp_message = "📊 **REPUTATION CHANGES**\n\n"
    
    for player_id, change_data in reputation_changes.items():
        player_data = game_session["players"].get(player_id, {})
        username = player_data.get("username", f"Player {player_id}")
        
        old_rp = change_data["before"]
        new_rp = change_data["after"]
        change = change_data["change"]
        
        if change > 0:
            rp_message += f"✅ **{username}**: {old_rp} → {new_rp} (+{change} RP)\n"
        elif change < 0:
            rp_message += f"❌ **{username}**: {old_rp} → {new_rp} ({change} RP)\n"
        else:
            rp_message += f"➖ **{username}**: {new_rp} RP (no change)\n"
        
        # Special status notifications
        if new_rp == 0:
            rp_message += f"   👻 *{username} is now a Ghost Viewer!*\n"
    
    rp_message += f"\n🎯 **Current Standings:**\n"
    
    # Show all player RP
    for player_id, player_data in game_session["players"].items():
        username = player_data.get("username", f"Player {player_id}")
        current_rp = game_session["player_reputation"].get(player_id, 3)
        
        status = ""
        if current_rp == 0:
            status = " 👻"
        elif player_id in game_session.get("shadow_banned_players", {}):
            status = " 🚫"
            
        rp_message += f"• **{username}**: {current_rp} RP{status}\n"
    
    await bot_context.bot.send_message(
        chat_id=game_session["chat_id"],
        text=rp_message
    )
```

---

## 🧪 **TESTING STRATEGY**

### **Unit Tests**
```python
# tests/test_snipe_timing.py
async def test_snipe_timing_restriction():
    """Test that snipes are only available on rounds 2 and 4."""
    # Test implementation here
    
# tests/test_educational_content.py  
async def test_drunk_educational_delivery():
    """Test that drunk receives and is reminded about educational content."""
    # Test implementation here

# tests/test_ai_headlines.py
async def test_ai_headline_generation():
    """Test AI headline generation and fallback."""
    # Test implementation here
```

### **Integration Tests**
- End-to-end game flow with all features
- Shadow ban communication blocking
- Educational content delivery timing
- Snipe availability across multiple rounds

---

## 📈 **ROLLOUT PLAN**

### **Phase 1: Core Fixes (Week 1)**
1. Implement snipe timing restriction
2. Basic educational content delivery
3. Enhanced shadow ban enforcement

### **Phase 2: Advanced Features (Week 2)**  
1. AI headline generation
2. Real-time RP display
3. Enhanced logging and analytics

### **Phase 3: Polish & Testing (Week 3)**
1. Comprehensive testing
2. Performance optimization  
3. Documentation updates
4. User feedback integration

---

## 🔧 **CONFIGURATION**

### **Environment Variables to Add**
```bash
# AI Features
OPENAI_API_KEY=your_openai_key_here
AI_HEADLINE_ENABLED=true

# Educational Features  
EDUCATIONAL_CONTENT_ENABLED=true
DRUNK_REMINDER_ENABLED=true

# Feature Flags
SNIPE_TIMING_ENFORCED=true
REALTIME_RP_DISPLAY=true
ENHANCED_SHADOW_BAN=true
```

---

## 🎯 **SUCCESS METRICS**

### **Technical Metrics**
- [ ] All unit tests passing
- [ ] Integration tests covering new features
- [ ] Performance impact < 10% increase in response time
- [ ] Error rate < 1% for new features

### **Game Experience Metrics**
- [ ] Educational content delivery rate > 95%
- [ ] Snipe timing enforcement working 100%
- [ ] Shadow ban communication blocking effective
- [ ] Player engagement with educational content

### **Educational Effectiveness**
- [ ] Players report learning from educational tips
- [ ] Improved accuracy in subsequent rounds after tips
- [ ] Positive feedback on learning experience

---

This implementation plan provides a roadmap to complete the Truth Wars refined game design. Each feature includes detailed technical specifications, testing requirements, and success criteria to ensure a high-quality implementation that matches the original design vision. 