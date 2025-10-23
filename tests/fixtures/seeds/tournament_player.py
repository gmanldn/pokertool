"""
Tournament Player Seeding
=========================

Seeds database with tournament player data (MTT specialist).
"""

import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from pokertool.database import PokerDatabase


def seed_tournament_player(db: PokerDatabase) -> None:
    """
    Seed database with tournament player data.

    Tournament player characteristics:
    - Primarily MTT hands (multi-table tournaments)
    - Mix of buy-in levels
    - Tournament-specific statistics (ITM rate, ROI)
    - Fewer hands than cash players (tournaments are slower)
    - Data includes tournament placements

    Args:
        db: PokerDatabase instance to seed
    """
    if not (hasattr(db, 'conn') and db.conn):
        return

    cursor = db.conn.cursor()

    # Tournament types
    tournament_types = ['MTT', 'SNG', 'Turbo', 'PKO']

    # Buy-in levels
    buy_ins = [5, 10, 25, 50, 100]

    # Generate 2,000 tournament hands (fewer than cash games)
    hands_to_generate = 2000

    try:
        # Create sample tournaments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                tournament_id TEXT PRIMARY KEY,
                timestamp TEXT,
                type TEXT,
                buy_in REAL,
                placement INTEGER,
                total_entries INTEGER,
                prize REAL,
                roi REAL
            )
        ''')

        # Create hands table with tournament reference
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hands (
                hand_id TEXT PRIMARY KEY,
                tournament_id TEXT,
                timestamp TEXT,
                site TEXT,
                stakes TEXT,
                result REAL,
                bb_won REAL,
                FOREIGN KEY(tournament_id) REFERENCES tournaments(tournament_id)
            )
        ''')

        # Generate sample tournaments
        base_time = datetime.now() - timedelta(days=90)  # 3 months ago
        tournament_count = 200

        for t in range(tournament_count):
            tournament_id = f'TOUR_{t:04d}'
            timestamp = base_time + timedelta(hours=t * 12)  # ~2 tournaments per day
            tournament_type = random.choice(tournament_types)
            buy_in = random.choice(buy_ins)
            total_entries = random.randint(50, 500)

            # Simulate ITM (In The Money) ~20% of the time
            is_itm = random.random() < 0.20

            if is_itm:
                # Place in top 15%
                placement = random.randint(1, int(total_entries * 0.15))

                # Calculate prize based on placement
                if placement == 1:
                    prize = buy_in * total_entries * 0.25  # 1st place ~25% of prize pool
                elif placement <= 3:
                    prize = buy_in * total_entries * 0.10  # Top 3
                else:
                    prize = buy_in * 1.5  # Min cash

                roi = ((prize - buy_in) / buy_in) * 100
            else:
                # Bust out
                placement = random.randint(int(total_entries * 0.15) + 1, total_entries)
                prize = 0
                roi = -100

            cursor.execute('''
                INSERT OR REPLACE INTO tournaments
                (tournament_id, timestamp, type, buy_in, placement, total_entries, prize, roi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (tournament_id, timestamp.isoformat(), tournament_type, buy_in,
                  placement, total_entries, prize, roi))

            # Generate hands for this tournament (average 10 hands per tournament)
            hands_per_tournament = random.randint(5, 15)

            for h in range(hands_per_tournament):
                if len(cursor.execute('SELECT COUNT(*) FROM hands').fetchone()) >= hands_to_generate:
                    break

                hand_id = f'{tournament_id}_H{h:03d}'
                hand_timestamp = timestamp + timedelta(minutes=h * 5)

                cursor.execute('''
                    INSERT OR REPLACE INTO hands
                    (hand_id, tournament_id, timestamp, site, stakes, result, bb_won)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (hand_id, tournament_id, hand_timestamp.isoformat(),
                      'PokerStars', f'T{buy_in}', 0, 0))

        db.conn.commit()

    except Exception as e:
        # If seeding fails, it's okay for tests
        pass
