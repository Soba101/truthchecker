"""
AI Headline Seeder

This utility generates a batch of AI-powered headlines (medium/hard difficulty)
and inserts them into the database.

Run from any async context, e.g. inside the main database seeding routine.
"""

from __future__ import annotations

import asyncio
import random
import json
from typing import List, Optional, Dict

from ..utils.logging_config import get_logger
from ..database.database import DatabaseSession
from ..database.models import Headline
from .headline_generator import get_headline_generator

logger = get_logger(__name__)


async def generate_and_seed_ai_headlines(count: int = 50, difficulties: Optional[List[str]] = None) -> int:
    """Generate *count* AI headlines and store them in the database.

    Args:
        count: Number of headlines to generate.
        difficulties: List of allowed difficulty levels. Defaults to ["medium", "hard"].

    Returns:
        Number of headlines successfully created.
    """

    if difficulties is None:
        difficulties = ["medium", "hard"]

    generator = get_headline_generator()
    if not generator.is_available():
        logger.warning("AI headline generator unavailable – skipping AI seeding")
        return 0

    categories = ["general", "health", "politics", "technology"]

    # Prepare async generation tasks
    tasks = []
    for i in range(count):
        difficulty = random.choice(difficulties)
        category = random.choice(categories)
        # Alternate real / fake for variety
        is_real = i % 2 == 0
        tasks.append(generator.generate_headline(difficulty=difficulty, category=category, is_real=is_real))

    results: List = await asyncio.gather(*tasks, return_exceptions=True)

    created = 0
    async with DatabaseSession() as session:
        for result in results:
            if isinstance(result, dict):
                # Default/derived values for optional fields to ensure completeness
                credibility = 8 if result["is_real"] else 2

                # Request additional metadata from OpenAI
                metadata = await _generate_metadata(generator.client, result["text"], result["is_real"])

                headline = Headline(
                    text=result["text"],
                    is_real=result["is_real"],
                    source=result.get("source"),
                    source_credibility_rating=credibility,
                    category=result.get("category", "general"),
                    difficulty=result.get("difficulty", "medium"),
                    explanation=result.get("explanation"),
                    detection_tips=metadata["detection_tips"],
                    teaches_concepts=metadata["teaches_concepts"],
                    red_flags=metadata["red_flags"],
                    verification_sources=metadata["verification_sources"],
                    created_by="ai_seed",
                )
                session.add(headline)
                created += 1
            elif isinstance(result, Exception):
                logger.error(f"AI headline generation failed: {result}")

        await session.commit()

    logger.info(f"Successfully seeded {created}/{count} AI generated headlines")
    return created


# ---------- Helper for additional metadata ----------

async def _generate_metadata(openai_client, headline: str, is_real: bool) -> Dict[str, List[str]]:
    """Ask OpenAI for detection tips, teaching concepts, red flags, verification sources.

    Returns sensible default lists if the request fails. """

    default = {
        "detection_tips": [
            "Cross-check with multiple reputable outlets",
            "Look for supporting data and expert quotes",
        ],
        "teaches_concepts": ["critical thinking"],
        "red_flags": [] if is_real else ["sensational language"],
        "verification_sources": ["fact-checking websites", "official statistics"],
    }

    if openai_client is None:
        return default

    try:
        truth_str = "REAL" if is_real else "FAKE"
        prompt = (
            "You are helping design an educational media-literacy game. For the headline below, "
            "return ONLY valid JSON with these keys: detection_tips, teaches_concepts, red_flags, verification_sources. "
            "Each value must be an array (2-4 short strings). If the headline is REAL, red_flags can be an empty array.\n\n"
            f"Headline ({truth_str}): \"{headline}\""
        )

        resp = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
            timeout=15.0,
        )

        content = resp.choices[0].message.content.strip()
        # There is a chance the model wraps JSON in code fences – strip them.
        if content.startswith("```"):
            content = content.strip("`")
            # remove possible language hint like json\n at start
            content = content.partition("\n")[2]
        data = json.loads(content)

        # Basic validation
        return {
            "detection_tips": data.get("detection_tips", default["detection_tips"]),
            "teaches_concepts": data.get("teaches_concepts", default["teaches_concepts"]),
            "red_flags": data.get("red_flags", default["red_flags"]),
            "verification_sources": data.get("verification_sources", default["verification_sources"]),
        }
    except Exception as e:
        logger.error(f"Failed to generate metadata for headline – using defaults: {e}")
        return default


if __name__ == "__main__":
    # Allow quick manual execution: `python -m bot.ai.ai_headline_seeder`
    asyncio.run(generate_and_seed_ai_headlines()) 