import requests
import json
from faker import Faker
import random
import time

# Initialize Faker to generate fake data
fake = Faker()

# The URL of the API endpoint on your Flask server
API_ENDPOINT = "http://127.0.0.1:5000/api/events"

# Define our suspicious player
SUSPICIOUS_PLAYER_ID = "player_foresaken"
NUM_HEADSHOTS = 5
NUM_MOVES = 2

def create_event(player_id, event_type):
    """Generates a specific game event."""
    return {
        'event_id': fake.uuid4(),
        'player_id': player_id,
        'event_type': event_type,
        'timestamp': fake.iso8601(),
        'details': {
            'location': f"({random.randint(0, 100)}, {random.randint(0, 100)})",
            'weapon': random.choice(['pistol', 'rifle', 'sniper']) if event_type == 'headshot' else None
        }
    }

def send_event(event):
    """Sends a single event to the API endpoint."""
    try:
        response = requests.post(API_ENDPOINT, json=event)
        if response.status_code == 201:
            print(f"Successfully sent event type: {event['event_type']} for player {event['player_id']}")
        else:
            print(f"Failed to send event. Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"Connection Error: Could not connect to the server at {API_ENDPOINT}.")
        print("Please ensure the Flask server (app.py) is running.")
        return False
    return True

if __name__ == "__main__":
    print(f"--- Starting Suspicious Player Test ---")
    print(f"Injecting test data for player: {SUSPICIOUS_PLAYER_ID}")
    
    # Send 5 'headshot' events
    print(f"\nSending {NUM_HEADSHOTS} 'headshot' events...")
    for _ in range(NUM_HEADSHOTS):
        event = create_event(SUSPICIOUS_PLAYER_ID, 'headshot')
        if not send_event(event):
            break
        time.sleep(0.1) # Small delay

    # Send 2 'player_move' events
    print(f"\nSending {NUM_MOVES} 'player_move' events...")
    for _ in range(NUM_MOVES):
        event = create_event(SUSPICIOUS_PLAYER_ID, 'player_move')
        if not send_event(event):
            break
        time.sleep(0.1) # Small delay

    print("\n--- Test Data Injected ---")
    print(f"Test player {SUSPICIOUS_PLAYER_ID} now has {NUM_HEADSHOTS} headshots and {NUM_MOVES} moves.")
    print("Ratio: ", NUM_HEADSHOTS / NUM_MOVES)
    print("\nPlease REFRESH your React dashboard (http://localhost:3000) to see the results.")