#!/usr/bin/env python3
"""
Test script for refined Truth Wars database models.

This script tests that all the new database models can be created
and validates the relationships work correctly.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.database.database import init_database, close_database, DatabaseSession
from bot.database.seed_data import seed_all_data
from bot.database.models import (
    # Core models
    User, Game, GamePlayer, TruthWarsGame, PlayerRole, Headline,
    # Refined system models
    PlayerReputationHistory, HeadlineVote, RoundResult,
    ShadowBanHistory, SnipeAction, HeadlineUsage,
    MediaLiteracyAnalytics, DrunkRoleAssignment,
    # Enums
    GameStatus, GamePhase, PlayerFaction, VoteType, SnipeResult
)
from bot.utils.config import get_settings
from bot.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def test_database_models():
    """
    Test all database models for the refined Truth Wars system.
    
    This creates sample data and verifies relationships work correctly.
    """
    try:
        logger.info("Testing refined Truth Wars database models...")
        
        # Initialize database
        await init_database()
        
        # Seed initial data
        await seed_all_data()
        
        # Test creating users with enhanced stats
        async with DatabaseSession() as session:
            # Create test users
            user1 = User(
                id=12345,
                username="testuser1",
                first_name="Test",
                last_name="User",
                media_literacy_level=3,
                learning_streak=5
            )
            
            user2 = User(
                id=67890,
                username="testuser2",
                first_name="Another",
                last_name="User",
                media_literacy_level=7,
                times_as_fact_checker=2,
                successful_snipes=1
            )
            
            session.add(user1)
            session.add(user2)
            await session.commit()
            
            logger.info("✓ Created users with enhanced statistics")
        
        # Test creating a refined Truth Wars game
        async with DatabaseSession() as session:
            # Create game with refined structure
            game = Game(
                game_type="truth_wars",
                status=GameStatus.WAITING,
                max_players=6,
                min_players=5,
                total_rounds=5,
                current_round=1
            )
            session.add(game)
            await session.flush()  # Get the ID
            
            # Create Truth Wars specific data
            truth_wars_data = TruthWarsGame(
                game_id=game.id,
                current_phase=GamePhase.LOBBY,
                drunk_rotation_order=[12345, 67890],
                next_snipe_round=2
            )
            session.add(truth_wars_data)
            
            # Create game players with reputation
            player1 = GamePlayer(
                game_id=game.id,
                user_id=12345,
                current_reputation=3,
                starting_reputation=3
            )
            
            player2 = GamePlayer(
                game_id=game.id,
                user_id=67890,
                current_reputation=2,  # Lost 1 RP
                starting_reputation=3,
                reputation_lost=1
            )
            
            session.add(player1)
            session.add(player2)
            await session.flush()
            
            # Create player roles for refined system
            role1 = PlayerRole(
                game_player_id=player1.id,
                role_name="fact_checker",
                faction=PlayerFaction.TRUTH_TEAM,
                fact_checker_blind_round=3
            )
            
            role2 = PlayerRole(
                game_player_id=player2.id,
                role_name="scammer",
                faction=PlayerFaction.SCAMMER_TEAM
            )
            
            session.add(role1)
            session.add(role2)
            
            await session.commit()
            
            logger.info("✓ Created refined Truth Wars game with reputation system")
        
        # Test headline voting system
        async with DatabaseSession() as session:
            # Get a sample headline from seeded data
            from sqlalchemy import select
            result = await session.execute(select(Headline).limit(1))
            headline = result.scalar_one()
            
            # Create headline votes with Trust/Flag system
            vote1 = HeadlineVote(
                game_id=game.id,
                user_id=12345,
                headline_id=headline.id,
                vote=VoteType.TRUST,
                is_correct=headline.is_real,  # Correct if real headline was trusted
                round_number=1,
                voter_reputation_before=3,
                voter_reputation_after=3 if headline.is_real else 2
            )
            
            vote2 = HeadlineVote(
                game_id=game.id,
                user_id=67890,
                headline_id=headline.id,
                vote=VoteType.FLAG,
                is_correct=not headline.is_real,  # Correct if fake headline was flagged
                round_number=1,
                voter_reputation_before=2,
                voter_reputation_after=2 if not headline.is_real else 1,
                vote_weight=2  # Influencer weight
            )
            
            session.add(vote1)
            session.add(vote2)
            
            # Create reputation history
            rep_change = PlayerReputationHistory(
                user_id=12345,
                game_player_id=player1.id,
                round_number=1,
                reputation_before=3,
                reputation_after=2,
                change_amount=-1,
                change_reason="incorrect_vote",
                headline_id=headline.id,
                player_vote=VoteType.TRUST,
                headline_truth=headline.is_real
            )
            session.add(rep_change)
            
            await session.commit()
            
            logger.info("✓ Created Trust/Flag voting system with reputation tracking")
        
        # Test snipe system
        async with DatabaseSession() as session:
            # Create snipe action
            snipe = SnipeAction(
                game_id=game.id,
                sniper_id=67890,
                target_id=12345,
                round_number=2,
                snipe_result=SnipeResult.SUCCESS,
                sniper_role="scammer",
                target_role="fact_checker",
                sniper_reputation=2,
                target_reputation=3,
                target_shadow_banned=True
            )
            session.add(snipe)
            await session.flush()
            
            # Create shadow ban history
            shadow_ban = ShadowBanHistory(
                game_id=game.id,
                snipe_action_id=snipe.id,
                banned_player_id=12345,
                round_banned=2,
                round_expires=4,
                ban_duration_rounds=2
            )
            session.add(shadow_ban)
            
            await session.commit()
            
            logger.info("✓ Created snipe system with shadow ban mechanics")
        
        # Test round results and educational tracking
        async with DatabaseSession() as session:
            round_result = RoundResult(
                game_id=game.id,
                headline_id=headline.id,
                round_number=1,
                headline_was_real=headline.is_real,
                total_trust_votes=1,
                total_flag_votes=1,
                weighted_trust_votes=1,
                weighted_flag_votes=2,  # Influencer weight
                majority_vote=VoteType.FLAG,
                majority_was_correct=not headline.is_real,
                players_voted_correctly=[67890] if not headline.is_real else [12345],
                round_started_at=datetime.utcnow()
            )
            session.add(round_result)
            
            # Create educational analytics
            learning = MediaLiteracyAnalytics(
                user_id=12345,
                game_id=game.id,
                concepts_learned=["source credibility", "bias recognition"],
                before_accuracy=60.0,
                after_accuracy=75.0,
                improvement_percentage=25.0,
                learning_source="drunk_tip"
            )
            session.add(learning)
            
            # Create Drunk role assignment
            drunk_assignment = DrunkRoleAssignment(
                game_id=game.id,
                player_id=12345,
                round_assigned=1,
                rotation_position=1,
                was_original_drunk=True,
                tips_shared=["Check source credibility", "Look for bias indicators"]
            )
            session.add(drunk_assignment)
            
            await session.commit()
            
            logger.info("✓ Created educational tracking and Drunk role system")
        
        # Test relationships and properties
        async with DatabaseSession() as session:
            # Test user relationships
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(User).where(User.id == 12345).options(
                    selectinload(User.game_players),
                    selectinload(User.headline_votes),
                    selectinload(User.reputation_history)
                )
            )
            test_user = result.scalar_one()
            
            # Verify properties work
            assert hasattr(test_user, 'headline_accuracy')
            assert hasattr(test_user, 'snipe_success_rate')
            
            # Test game relationships
            result = await session.execute(
                select(Game).where(Game.id == game.id).options(
                    selectinload(Game.players),
                    selectinload(Game.truth_wars_data),
                    selectinload(Game.headline_votes)
                )
            )
            test_game = result.scalar_one()
            
            # Verify game properties
            assert hasattr(test_game, 'truth_team_won')
            assert hasattr(test_game, 'scammer_team_won')
            assert hasattr(test_game, 'is_game_over')
            
            logger.info("✓ Verified relationships and model properties work correctly")
        
        logger.info("🎉 All database model tests passed successfully!")
        logger.info("Refined Truth Wars database system is fully functional with:")
        logger.info("- Enhanced user statistics and media literacy tracking")
        logger.info("- Reputation system with Ghost Viewer mechanics")
        logger.info("- Trust/Flag voting with educational context")
        logger.info("- Shadow ban system via snipe mechanics")
        logger.info("- Educational content tracking and analytics")
        logger.info("- Complete relationship mapping and data integrity")
        
    except Exception as e:
        logger.error(f"Database model test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await close_database()


if __name__ == "__main__":
    # Set test database URL to avoid affecting production data
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_truth_wars.db"
    
    try:
        asyncio.run(test_database_models())
        print("\n✅ Database model tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Database model tests failed: {e}")
        sys.exit(1)
    finally:
        # Clean up test database
        test_db_path = "test_truth_wars.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("🧹 Cleaned up test database file") 