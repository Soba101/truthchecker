"""
AI Headline Generator

This module uses OpenAI's GPT models to generate realistic fake and real headlines
for the Truth Wars game, providing dynamic content that improves educational value.
"""

import openai
import random
import asyncio
from typing import Dict, List, Optional, Any
from ..utils.config import get_settings
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class HeadlineGenerator:
    """
    AI-powered headline generator for Truth Wars.
    
    Uses OpenAI's GPT models to create realistic headlines that are either
    true or false, with educational explanations for each one.
    """
    
    def __init__(self):
        """Initialize the headline generator with OpenAI configuration."""
        self.settings = get_settings()
        self.client = None
        
        # Only initialize OpenAI if API key is provided
        if self.settings.openai_api_key:
            try:
                self.client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("No OpenAI API key provided - AI headlines disabled")
    
    def is_available(self) -> bool:
        """Check if AI headline generation is available."""
        return (
            self.client is not None 
            and self.settings.ai_headline_enabled 
            and self.settings.openai_api_key
        )
    
    async def generate_headline(
        self, 
        difficulty: str = "medium", 
        category: str = "general", 
        is_real: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a realistic headline using AI.
        
        Args:
            difficulty: Difficulty level ("easy", "medium", "hard")
            category: Category of news ("general", "health", "politics", "technology")
            is_real: Whether to generate real or fake news (None = random)
            
        Returns:
            Dict with headline data or None if generation fails
        """
        if not self.is_available():
            logger.debug("AI headline generation not available")
            return None
        
        # Randomly determine if headline should be real or fake
        if is_real is None:
            is_real = random.choice([True, False])
        
        try:
            # Generate the headline text
            headline_text = await self._generate_headline_text(difficulty, category, is_real)
            if not headline_text:
                return None
            
            # Generate educational explanation
            explanation = await self._generate_explanation(headline_text, is_real, difficulty)
            
            # Generate source attribution
            source = self._generate_source_attribution(is_real, category)
            
            return {
                "text": headline_text,
                "is_real": is_real,
                "source": source,
                "explanation": explanation,
                "category": category,
                "difficulty": difficulty,
                "ai_generated": True
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI headline: {e}")
            return None
    
    async def _generate_headline_text(
        self, 
        difficulty: str, 
        category: str, 
        is_real: bool
    ) -> Optional[str]:
        """Generate the actual headline text using OpenAI."""
        
        # Define difficulty-specific prompts
        difficulty_prompts = {
            "easy": {
                "fake": "obviously fake news that most people can identify as false",
                "real": "straightforward real news that is clearly factual"
            },
            "medium": {
                "fake": "moderately believable fake news that requires some critical thinking to identify",
                "real": "real news that might seem surprising but is actually true"
            },
            "hard": {
                "fake": "very sophisticated fake news that's difficult to distinguish from real news",
                "real": "real news that sounds almost too strange to be true but is factual"
            }
        }
        
        # Define category contexts
        category_contexts = {
            "health": "health, medicine, wellness, or medical research",
            "politics": "political news, government, or policy",
            "technology": "technology, science, innovation, or research", 
            "general": "general news from any topic"
        }
        
        # Build the prompt
        news_type = "real" if is_real else "fake"
        difficulty_desc = difficulty_prompts.get(difficulty, difficulty_prompts["medium"])[news_type]
        category_desc = category_contexts.get(category, category_contexts["general"])
        
        if is_real:
            prompt = f"""Generate a real, factual news headline about {category_desc}. 
            
            Requirements:
            - Must be {difficulty_desc}
            - Actually true and verifiable
            - Realistic news headline format
            - Appropriate for educational media literacy game
            - Between 8-15 words
            
            Return ONLY the headline text, nothing else."""
        else:
            prompt = f"""Generate a fake news headline about {category_desc}. 
            
            Requirements:
            - Must be {difficulty_desc}
            - Realistic-sounding but completely false
            - Designed for media literacy education
            - Should have red flags that critical thinkers could identify
            - Between 8-15 words
            
            Return ONLY the headline text, nothing else."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.8,
                timeout=15.0  # 15 second timeout
            )
            
            headline_text = response.choices[0].message.content.strip()
            
            # Clean up the headline (remove quotes if present)
            headline_text = headline_text.strip('"\'')
            
            logger.info(f"Generated {'real' if is_real else 'fake'} {difficulty} headline: {headline_text[:50]}...")
            return headline_text
            
        except asyncio.TimeoutError:
            logger.error("OpenAI request timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to generate headline text: {e}")
            return None
    
    async def _generate_explanation(
        self, 
        headline: str, 
        is_real: bool, 
        difficulty: str
    ) -> str:
        """Generate educational explanation for why headline is real/fake."""
        
        if is_real:
            prompt = f"""Explain why this headline is REAL/TRUE in 2-3 sentences for educational purposes.
            
            Focus on:
            - What makes it credible
            - How someone could verify it
            - Why it's realistic
            
            Headline: "{headline}"
            
            Keep explanation educational and encouraging of critical thinking."""
        else:
            prompt = f"""Explain why this headline is FAKE in 2-3 sentences for educational purposes.
            
            Focus on:
            - Red flags that indicate it's false
            - How someone could fact-check it
            - What makes it suspicious
            
            Headline: "{headline}"
            
            Keep explanation educational for media literacy learning."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7,
                timeout=15.0
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.debug(f"Generated explanation for headline: {len(explanation)} characters")
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            # Fallback explanation
            if is_real:
                return "This headline is real. Look for credible sources and cross-reference with multiple news outlets to verify."
            else:
                return "This headline is fake. Always check sources, look for emotional language, and verify with fact-checking websites."
    
    def _generate_source_attribution(self, is_real: bool, category: str) -> str:
        """Generate realistic source attribution for the headline."""
        
        if is_real:
            # Real news sources by category
            real_sources = {
                "health": ["Mayo Clinic News", "Harvard Health", "WebMD News", "Medical News Today"],
                "politics": ["Reuters", "Associated Press", "BBC News", "NPR"],
                "technology": ["TechCrunch", "Wired", "MIT Technology Review", "Science Daily"],
                "general": ["Reuters", "Associated Press", "BBC News", "NPR", "CNN"]
            }
            sources = real_sources.get(category, real_sources["general"])
        else:
            # Fake/suspicious source names that sound plausible but aren't real major outlets
            fake_sources = [
                "Daily Truth News", "Global Update Network", "Breaking News 24/7",
                "World Facts Today", "Real Story News", "Truth Central",
                "Independent News Wire", "Citizens Report", "Freedom News Network"
            ]
            sources = fake_sources
        
        return f"AI Generated ({random.choice(sources)})"
    
    async def generate_batch_headlines(
        self, 
        count: int = 5, 
        difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple headlines in one batch for efficiency.
        
        Args:
            count: Number of headlines to generate
            difficulty: Difficulty level for all headlines
            
        Returns:
            List of headline dictionaries
        """
        if not self.is_available():
            return []
        
        headlines = []
        categories = ["general", "health", "politics", "technology"]
        
        # Use asyncio.gather for concurrent generation
        tasks = []
        for i in range(count):
            category = random.choice(categories)
            is_real = i % 2 == 0  # Alternate between real and fake
            
            task = self.generate_headline(difficulty, category, is_real)
            tasks.append(task)
        
        try:
            # Wait for all headlines to generate concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):  # Successful generation
                    headlines.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Failed to generate headline in batch: {result}")
            
            logger.info(f"Generated {len(headlines)}/{count} headlines in batch")
            return headlines
            
        except Exception as e:
            logger.error(f"Failed to generate headline batch: {e}")
            return headlines


# Create a singleton instance for easy access
_headline_generator = None

def get_headline_generator() -> HeadlineGenerator:
    """Get the singleton headline generator instance."""
    global _headline_generator
    if _headline_generator is None:
        _headline_generator = HeadlineGenerator()
    return _headline_generator 