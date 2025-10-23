import pandas as pd
from app import app, db, Event  # We import our existing app and models
import json

def analyze_data():
    """
    Fetches all events from the database and runs a basic
    analysis using pandas.
    """
    
    # We use app.app_context() to make sure we can access the database
    with app.app_context():
        # Query the database for all events
        events = Event.query.all()
        
        if not events:
            print("No data in the database to analyze.")
            print("Run 'python data_simulator.py' a few times to generate data.")
            return

        # Convert the list of Event objects into a list of dictionaries
        data = []
        for event in events:
            data.append({
                'id': event.id,
                'event_id': event.event_id,
                'player_id': event.player_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp,
                # We also need to parse the 'details' JSON string
                'details': json.loads(event.details)
            })

        # Create a pandas DataFrame from our list of dictionaries
        df = pd.DataFrame(data)
        
        # --- Basic Analysis ---
        print("--- Database Events Analysis ---")
        
        print("\n[DataFrame Info]")
        # .info() shows data types and non-null counts
        df.info()
        
        print("\n[Event Type Counts]")
        # .value_counts() shows the frequency of each event type
        print(df['event_type'].value_counts())
        
        print("\n[Sample Data (First 5 Rows)]")
        # .head() shows the first 5 rows of your data
        print(df.head())

if __name__ == "__main__":
    analyze_data()
