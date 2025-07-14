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
        Always uses 'hard' difficulty for maximum challenge.
        Always generates headlines about any topic (not limited to a category).
        """
        if not self.is_available():
            logger.debug("AI headline generation not available")
            return None
        # Always use hard difficulty for maximum challenge
        difficulty = "hard"
        # Always use 'any' category for maximum variety
        category = "any"
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
        """Generate the actual headline text using OpenAI.
        Always uses a broad, open-ended prompt for any topic.
        """
        # Build the prompt (no category context)
        if is_real:
            prompt = f"""Generate a real, factual news headline about any topic.
            
            Requirements:
            - Must be very hard to tell if it's real or fake
            - Actually true and verifiable
            - Realistic news headline format
            - Appropriate for educational media literacy game
            - Between 8-15 words
            
            Return ONLY the headline text, nothing else."""
        else:
            prompt = f"""Generate a FAKE news headline about any topic.
            
            Requirements:
            - Make it extremely plausible and subtle, so that it is very hard to tell if it is real or fake
            - Do NOT use satire, humor, or outlandish claims
            - The headline should sound like something that could genuinely appear in a reputable news outlet
            - Avoid obvious red flags or giveaways
            - Should be as realistic as possible, but still completely false
            - Appropriate for an educational media literacy game
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
        """Generate realistic source attribution for the headline.
        Picks randomly from all reputable sources, since topic is open.
        """
        all_sources = [
            "Mayo Clinic News", "Harvard Health", "WebMD News", "Medical News Today", "The Lancet", "Nature Medicine", "BMJ", "CDC News",
            "Reuters", "Associated Press", "BBC News", "NPR", "The Guardian", "New York Times", "Washington Post", "Politico",
            "TechCrunch", "Wired", "MIT Technology Review", "Science Daily", "The Verge", "Ars Technica", "IEEE Spectrum", "Nature",
            "CNN", "Wall Street Journal"
        ]
        return random.choice(all_sources)
    
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