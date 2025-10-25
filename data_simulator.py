import requests
import json
from faker import Faker
import random
import time
# --- Import datetime ---
from datetime import datetime, timezone

# Initialize Faker
fake = Faker()

# The URL of the API endpoint on your Flask server
API_ENDPOINT = "http://127.0.0.1:5000/api/events"

def generate_game_event():
    """Generates a single fake game event with the current timestamp."""
    event_types = ['player_login', 'player_logout', 'player_move', 'item_pickup', 'headshot']
    selected_event_type = random.choice(event_types)

    # --- UPDATED: Generate standard YYYY-MM-DDTHH:MM:SSZ format ---
    current_time_utc_dt = datetime.now(timezone.utc)
    # Use isoformat, specify seconds, and replace +00:00 offset with Z if present
    current_time_utc = current_time_utc_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
    # --- END UPDATE ---

    # Create a dictionary representing the event
    event = {
        'event_id': fake.uuid4(),
        'player_id': f"player_{random.randint(1000, 9999)}",
        'event_type': selected_event_type,
        'timestamp': current_time_utc, # <-- Use the clean timestamp
        'details': {
            'location': f"({random.randint(0, 100)}, {random.randint(0, 100)})",
            'weapon': random.choice(['pistol', 'rifle', 'sniper']) if selected_event_type == 'headshot' else None
        }
    }
    # Ensure details only contains weapon if it's relevant
    if event['details'].get('weapon') is None: # Use .get() for safer access
       if 'weapon' in event['details']:
            del event['details']['weapon'] # Remove weapon key if None

    return event

def send_event(event):
    """Sends a single event to the API endpoint."""
    try:
        response = requests.post(API_ENDPOINT, json=event)
        if response.status_code == 201:
            print(f"Successfully sent event: {event['event_id']} ({event['event_type']}) at {event['timestamp']}")
        else:
            print(f"Failed to send event. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: Could not connect to the server at {API_ENDPOINT}.")
        print("Please ensure the Flask server (app.py) is running.")

if __name__ == "__main__":
    game_event = generate_game_event()
    send_event(game_event)

