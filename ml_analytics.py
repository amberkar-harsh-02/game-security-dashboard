import pandas as pd
from app import app, db, Event  # We import our existing app and models
import json
import numpy as np # We'll need numpy for safe division

def analyze_data():
    """
    Fetches all events from the database and runs an anomaly
    detection analysis to find suspicious players.
    """
    
    with app.app_context():
        events = Event.query.all()
        
        if not events:
            print("No data in the database to analyze.")
            print("Run 'python data_simulator.py' a few times to generate data.")
            return

        data = []
        for event in events:
            data.append({
                'id': event.id,
                'event_id': event.event_id,
                'player_id': event.player_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp,
                'details': json.loads(event.details)
            })

        df = pd.DataFrame(data)
        
        # --- Basic Analysis (from last step) ---
        print("--- Database Events Analysis ---")
        print(f"Total events processed: {len(df)}")
        print("\n[Event Type Counts]")
        print(df['event_type'].value_counts())
        
        
        # --- NEW: Anomaly Detection ---
        print("\n\n--- Anomaly Detection Analysis ---")
        
        # 1. Group by player_id and count specific events
        # We create a new DataFrame where each row is a player
        player_stats = df.groupby('player_id')['event_type'].value_counts().unstack(fill_value=0)
        
        # 2. Engineer our "suspicion" feature
        # We'll define a simple metric: Headshot-to-Move Ratio
        # We use np.where to avoid dividing by zero for players with 0 moves
        player_stats['hs_per_move_ratio'] = np.where(
            player_stats['player_move'] > 0, 
            player_stats['headshot'] / player_stats['player_move'],
            0 # Give players with 0 moves a ratio of 0
        )
        
        # 3. Define our "suspicious" threshold
        # Any player with more headshots than moves is suspicious
        SUSPICIOUS_THRESHOLD = 1.0
        
        # 4. Filter for suspicious players
        suspicious_players = player_stats[
            player_stats['hs_per_move_ratio'] > SUSPICIOUS_THRESHOLD
        ].sort_values(by='hs_per_move_ratio', ascending=False)
        
        
        # --- Display Results ---
        if suspicious_players.empty:
            print("\n[Result: No suspicious players found]")
        else:
            print(f"\n[Result: Found {len(suspicious_players)} Suspicious Players]")
            print(suspicious_players)
            
        print("\n[All Player Stats (for comparison)]")
        # Print all stats so you can see the normal players too
        print(player_stats.sort_values(by='hs_per_move_ratio', ascending=False).head(10))


if __name__ == "__main__":
    analyze_data()
