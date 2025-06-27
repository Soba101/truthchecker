"""
Database Seeding for Truth Wars Refined System

This module provides functions to seed the database with initial data
including educational headlines, media literacy content, and configuration.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import select

from .database import DatabaseSession
from .models import Headline, User
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


# Sample headlines with educational value for refined Truth Wars system
INITIAL_HEADLINES = [
    {
        "text": "Scientists discover chocolate consumption linked to improved memory function in adults",
        "is_real": True,
        "source": "Nature Neuroscience",
        "source_credibility_rating": 9,
        "category": "health",
        "difficulty": "easy",
        "explanation": "This is based on a real study published in Nature Neuroscience about flavonoids in chocolate improving cognitive function.",
        "detection_tips": [
            "Check if the source is a reputable scientific journal",
            "Look for peer-reviewed research backing the claim",
            "Scientific claims should be measured, not exaggerated"
        ],
        "teaches_concepts": ["source credibility", "scientific method", "peer review"],
        "red_flags": [],
        "verification_sources": ["PubMed", "Nature.com", "university research databases"]
    },
    {
        "text": "Local man trains squirrels to deliver mail, postal service considering partnership",
        "is_real": False,
        "source": "The Onion",
        "source_credibility_rating": 2,
        "category": "general",
        "difficulty": "easy",
        "explanation": "This is a satirical headline from The Onion, a well-known satire publication that creates humorous fake news.",
        "detection_tips": [
            "Recognize satirical news sources like The Onion",
            "Absurd scenarios often indicate satire",
            "Check if other credible sources report similar stories"
        ],
        "teaches_concepts": ["satirical content", "source recognition", "critical thinking"],
        "red_flags": ["absurd scenario", "satirical source", "no corroborating reports"],
        "verification_sources": ["Snopes", "fact-checking websites", "mainstream news"]
    },
    {
        "text": "New AI system achieves 95% accuracy in detecting deepfake videos",
        "is_real": True,
        "source": "MIT Technology Review",
        "source_credibility_rating": 8,
        "category": "technology",
        "difficulty": "medium",
        "explanation": "This reflects real ongoing research in AI-powered deepfake detection, though the specific percentage may vary.",
        "detection_tips": [
            "Tech advances are incremental, not revolutionary overnight",
            "Look for specific research institutions or companies involved",
            "Check if the advancement seems technically plausible"
        ],
        "teaches_concepts": ["technology reporting", "credible tech journalism", "research verification"],
        "red_flags": [],
        "verification_sources": ["university research", "tech company announcements", "peer-reviewed papers"]
    },
    {
        "text": "Doctors hate this one weird trick: Woman loses 50 pounds in 2 weeks using kitchen spice",
        "is_real": False,
        "source": "HealthClickbait.com",
        "source_credibility_rating": 1,
        "category": "health",
        "difficulty": "easy",
        "explanation": "Classic clickbait format promising unrealistic results. Rapid weight loss claims are typically scams or dangerous.",
        "detection_tips": [
            "Beware of 'doctors hate this trick' language",
            "Unrealistic weight loss claims are red flags",
            "Check for medical professional endorsement"
        ],
        "teaches_concepts": ["clickbait recognition", "health misinformation", "unrealistic claims"],
        "red_flags": ["clickbait language", "unrealistic claims", "suspicious source", "no medical backing"],
        "verification_sources": ["medical professionals", "health organizations", "FDA"]
    },
    {
        "text": "Climate change accelerated melting causes Arctic ice to reach record low levels",
        "is_real": True,
        "source": "National Geographic",
        "source_credibility_rating": 9,
        "category": "environment",
        "difficulty": "medium",
        "explanation": "Climate data consistently shows accelerating ice loss in the Arctic, documented by multiple scientific organizations.",
        "detection_tips": [
            "Climate science has strong consensus among scientists",
            "Look for data from meteorological organizations",
            "Multiple independent sources should report similar findings"
        ],
        "teaches_concepts": ["scientific consensus", "climate data interpretation", "credible environmental reporting"],
        "red_flags": [],
        "verification_sources": ["NOAA", "NASA", "IPCC reports", "scientific journals"]
    },
    {
        "text": "Vaccines contain microchips that allow government tracking of citizens",
        "is_real": False,
        "source": "TruthSeeker.blog",
        "source_credibility_rating": 1,
        "category": "health",
        "difficulty": "medium",
        "explanation": "This is a widely debunked conspiracy theory with no scientific basis. Vaccines are extensively tested and monitored.",
        "detection_tips": [
            "Conspiracy theories often lack credible evidence",
            "Medical claims should have peer-reviewed support",
            "Check official health organization statements"
        ],
        "teaches_concepts": ["conspiracy theory identification", "medical misinformation", "authority credibility"],
        "red_flags": ["conspiracy language", "lack of evidence", "contradicts medical consensus", "unreliable source"],
        "verification_sources": ["WHO", "CDC", "medical journals", "fact-checkers"]
    },
    {
        "text": "Stock market reaches new all-time high as investor confidence grows",
        "is_real": True,
        "source": "Reuters",
        "source_credibility_rating": 8,
        "category": "business",
        "difficulty": "medium",
        "explanation": "Financial news about market performance is typically factual and can be verified through market data.",
        "detection_tips": [
            "Financial news is usually verifiable through market data",
            "Multiple financial sources should report similar information",
            "Check official market indices and trading platforms"
        ],
        "teaches_concepts": ["financial reporting", "market data verification", "business journalism"],
        "red_flags": [],
        "verification_sources": ["stock exchanges", "financial data providers", "multiple news sources"]
    },
    {
        "text": "Eating this one fruit daily will make you immortal, ancient secret revealed",
        "is_real": False,
        "source": "HealthMiracles.net",
        "source_credibility_rating": 1,
        "category": "health",
        "difficulty": "easy",
        "explanation": "Claims of immortality through diet are impossible and classic misinformation tactics targeting health concerns.",
        "detection_tips": [
            "Claims of immortality or miracle cures are always false",
            "Be skeptical of 'ancient secrets' marketing",
            "No single food provides miraculous health benefits"
        ],
        "teaches_concepts": ["health scam recognition", "impossible claims", "marketing tactics"],
        "red_flags": ["impossible claims", "miracle cure language", "ancient secret appeal", "unreliable source"],
        "verification_sources": ["medical professionals", "nutrition scientists", "health organizations"]
    },
    {
        "text": "Major earthquake strikes coastal region, tsunami warning issued for Pacific",
        "is_real": True,
        "source": "Associated Press",
        "source_credibility_rating": 9,
        "category": "news",
        "difficulty": "hard",
        "explanation": "Emergency news requires verification but legitimate sources report breaking news quickly with updates as information becomes available.",
        "detection_tips": [
            "Breaking news should be verified across multiple sources",
            "Official emergency services provide authoritative information",
            "Be cautious of unverified social media reports"
        ],
        "teaches_concepts": ["breaking news verification", "emergency information", "source triangulation"],
        "red_flags": [],
        "verification_sources": ["government emergency services", "seismic monitoring agencies", "multiple news outlets"]
    },
    {
        "text": "Celebrity spotted eating pineapple pizza, fans demand boycott of all Italian restaurants",
        "is_real": False,
        "source": "CelebGossip24.com",
        "source_credibility_rating": 2,
        "category": "entertainment",
        "difficulty": "medium",
        "explanation": "While celebrities do get photographed eating, the extreme reaction described is fabricated for engagement and clicks.",
        "detection_tips": [
            "Celebrity gossip often exaggerates reactions",
            "Check if mainstream entertainment news reports the story",
            "Extreme public reactions are often fabricated"
        ],
        "teaches_concepts": ["entertainment misinformation", "engagement-driven content", "proportionality assessment"],
        "red_flags": ["exaggerated reactions", "gossip source", "manufactured controversy"],
        "verification_sources": ["entertainment news outlets", "celebrity social media", "verified reporting"]
    }
]

# Educational tips that Drunk players can share
MEDIA_LITERACY_TIPS = [
    {
        "category": "source_verification",
        "tip": "Always check the 'About' section of websites to understand who's behind the information",
        "explanation": "Legitimate news sources clearly identify their organization, funding, and editorial policies"
    },
    {
        "category": "bias_recognition", 
        "tip": "Look for emotional language and one-sided reporting - good journalism presents multiple perspectives",
        "explanation": "Biased sources use charged language and ignore opposing viewpoints"
    },
    {
        "category": "fact_checking",
        "tip": "Use the SIFT method: Stop, Investigate source, Find better coverage, Trace claims",
        "explanation": "This systematic approach helps verify information before sharing it"
    },
    {
        "category": "scientific_claims",
        "tip": "Real scientific breakthroughs are reported by multiple credible sources, not just one website",
        "explanation": "Scientific consensus builds over time through peer review and replication"
    },
    {
        "category": "clickbait_detection",
        "tip": "Headlines with 'You won't believe' or 'Doctors hate this' are usually clickbait",
        "explanation": "Legitimate news uses clear, informative headlines rather than emotional manipulation"
    }
]


async def seed_headlines() -> None:
    """
    Seed the database with initial educational headlines.
    
    This creates a diverse set of headlines across difficulty levels
    and categories for the refined Truth Wars system.
    """
    try:
        async with DatabaseSession() as session:
            # Check if headlines already exist
            result = await session.execute(select(Headline).limit(1))
            existing_headline = result.scalar_one_or_none()
            
            if existing_headline:
                logger.info("Headlines already exist in database, skipping seeding")
                return
            
            logger.info("Seeding database with initial headlines...")
            
            headlines_created = 0
            for headline_data in INITIAL_HEADLINES:
                headline = Headline(
                    text=headline_data["text"],
                    is_real=headline_data["is_real"],
                    source=headline_data["source"],
                    source_credibility_rating=headline_data.get("source_credibility_rating"),
                    category=headline_data["category"],
                    difficulty=headline_data["difficulty"],
                    explanation=headline_data["explanation"],
                    detection_tips=headline_data.get("detection_tips", []),
                    teaches_concepts=headline_data.get("teaches_concepts", []),
                    red_flags=headline_data.get("red_flags", []),
                    verification_sources=headline_data.get("verification_sources", []),
                    created_by="system_seed"
                )
                
                session.add(headline)
                headlines_created += 1
            
            await session.commit()
            logger.info(f"Successfully seeded {headlines_created} headlines into database")
            
            # Log breakdown by difficulty
            easy_count = len([h for h in INITIAL_HEADLINES if h["difficulty"] == "easy"])
            medium_count = len([h for h in INITIAL_HEADLINES if h["difficulty"] == "medium"])
            hard_count = len([h for h in INITIAL_HEADLINES if h["difficulty"] == "hard"])
            
            logger.info(f"Headline difficulty distribution: Easy={easy_count}, Medium={medium_count}, Hard={hard_count}")
            
    except Exception as e:
        logger.error(f"Failed to seed headlines: {e}")
        raise


async def create_admin_user(user_id: int, username: str = None) -> None:
    """
    Create an admin user for system management.
    
    Args:
        user_id: Telegram user ID for the admin
        username: Optional Telegram username
    """
    try:
        async with DatabaseSession() as session:
            # Check if user already exists
            result = await session.execute(select(User).where(User.id == user_id))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # Update existing user to admin
                existing_user.is_admin = True
                logger.info(f"Updated existing user {user_id} to admin status")
            else:
                # Create new admin user
                admin_user = User(
                    id=user_id,
                    username=username,
                    is_admin=True,
                    media_literacy_level=10  # Max level for admins
                )
                session.add(admin_user)
                logger.info(f"Created new admin user {user_id}")
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        raise


async def seed_all_data() -> None:
    """
    Seed all initial data for the refined Truth Wars system.
    
    This function should be called after database initialization
    to populate the system with initial content.
    """
    logger.info("Starting database seeding for refined Truth Wars system...")
    
    try:
        # Seed headlines
        await seed_headlines()
        
        logger.info("Database seeding completed successfully!")
        logger.info(f"System ready with {len(INITIAL_HEADLINES)} headlines and {len(MEDIA_LITERACY_TIPS)} educational tips")
        
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise


async def get_media_literacy_tip(category: str = None) -> Dict[str, Any]:
    """
    Get a random media literacy tip for educational content.
    
    Args:
        category: Optional category filter
        
    Returns:
        Dict containing tip information
    """
    import random
    
    tips = MEDIA_LITERACY_TIPS
    if category:
        tips = [tip for tip in tips if tip["category"] == category]
    
    if not tips:
        tips = MEDIA_LITERACY_TIPS  # Fallback to all tips
    
    return random.choice(tips)


if __name__ == "__main__":
    # Allow running this file directly for testing
    asyncio.run(seed_all_data()) 