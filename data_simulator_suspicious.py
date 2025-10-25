import requests
import json
import random
import time
# --- Import datetime ---
from datetime import datetime, timezone
from faker import Faker

fake = Faker()

# Your API endpoint
API_ENDPOINT = "http://127.0.0.1:5000/api/events"

# Define the suspicious player ID
SUSPICIOUS_PLAYER_ID = "player_tenz"

def send_test_event(event_type):
    """Generates and sends a test event for the suspicious player."""
    # --- UPDATED: Generate standard YYYY-MM-DDTHH:MM:SSZ format ---
    current_time_utc_dt = datetime.now(timezone.utc)
    # Use isoformat, specify seconds, and replace +00:00 offset with Z if present
    current_time_utc = current_time_utc_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
    # --- END UPDATE ---

    event = {
        'event_id': fake.uuid4(),
        'player_id': SUSPICIOUS_PLAYER_ID,
        'event_type': event_type,
        'timestamp': current_time_utc, # Use clean time
        'details': {
            'location': f"({random.randint(0, 100)}, {random.randint(0, 100)})"
        }
    }
    # Add weapon only for headshots
    if event_type == 'headshot':
        event['details']['weapon'] = 'sniper' # Be consistent

    try:
        response = requests.post(API_ENDPOINT, json=event)
        if response.status_code == 201:
            print(f"Sent {event_type} event for {SUSPICIOUS_PLAYER_ID} at {current_time_utc}")
        else:
            print(f"Failed to send {event_type} event. Status: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("Connection Error: Flask server not running?")
        return False # Indicate failure
    return True # Indicate success

if __name__ == "__main__":
    print(f"--- Sending test data for suspicious player: {SUSPICIOUS_PLAYER_ID} ---")

    # Send 5 headshots
    print("\nSending 5 headshot events...")
    success = True
    for _ in range(5):
        if not send_test_event('headshot'):
            success = False
            break
        time.sleep(0.1) # Small delay

    # Send 2 moves
    if success:
        print("\nSending 2 move events...")
        for _ in range(2):
            if not send_test_event('player_move'):
                success = False
                break
            time.sleep(0.1)

    if success:
        print("\n--- Test data sent successfully ---")
    else:
        print("\n--- Failed to send all test data ---")

