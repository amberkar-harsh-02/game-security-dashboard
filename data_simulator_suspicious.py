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
SUSPICIOUS_PLAYER_ID = "player_f0rsaken" # Or your preferred test ID

# --- CoD Weapons & Context ---
COD_WEAPONS = [
    # ARs
    'M4A1', 'AK-47', 'SCAR-H', 'RAM-7', 'Kilo 141', 'M13',
    # SMGs
    'MP5', 'UMP45', 'Vector', 'P90', 'MP7', 'AUG',
    # Snipers
    'Intervention', 'AX-50', 'HDR', 'Dragunov', 'Rytec AMR',
    # Pistols
    'M1911', '.50 GS', 'X16', 'Renetti',
    # Launchers / Melee / Lethals
    'RPG-7', 'Combat Knife', 'Frag Grenade', 'Semtex', 'Throwing Knife'
]
MAPS = ['Shoot House', 'Hackney Yard', 'Crash', 'Shipment']
MODES = ['TDM', 'Domination', 'Hardpoint', 'S&D']
# --- END Context ---


def send_test_event(event_type):
    """Generates and sends a test event for the suspicious player with CoD details."""
    # --- Use standard YYYY-MM-DDTHH:MM:SSZ format ---
    current_time_utc_dt = datetime.now(timezone.utc)
    current_time_utc = current_time_utc_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
    # --- End Time Format ---

    event = {
        'event_id': fake.uuid4(),
        'player_id': SUSPICIOUS_PLAYER_ID,
        'event_type': event_type,
        'timestamp': current_time_utc, # Use current time
        'details': {
            'map': random.choice(MAPS), # Add map context
            'mode': random.choice(MODES)  # Add game mode
        }
    }
    # Add specific details based on event type
    if event_type == 'headshot' or event_type == 'kill':
        # Use a weapon suitable for headshots/kills
        event['details']['weapon'] = random.choice([w for w in COD_WEAPONS if w not in ['RPG-7', 'Combat Knife', 'Frag Grenade', 'Semtex', 'Throwing Knife']])
        event['details']['victim_id'] = f"player_{random.randint(1000, 9999)}"
        while event['details']['victim_id'] == SUSPICIOUS_PLAYER_ID: # Ensure not self-kill
             event['details']['victim_id'] = f"player_{random.randint(1000, 9999)}"
    elif event_type == 'player_move':
         event['details']['location_start'] = f"({random.randint(0, 100)}, {random.randint(0, 100)})"
         event['details']['location_end'] = f"({random.randint(0, 100)}, {random.randint(0, 100)})"
    elif event_type == 'death':
        event['details']['killer_id'] = f"player_{random.randint(1000, 9999)}"
        while event['details']['killer_id'] == SUSPICIOUS_PLAYER_ID: # Ensure not self-death source
            event['details']['killer_id'] = f"player_{random.randint(1000, 9999)}"
        event['details']['weapon'] = random.choice(COD_WEAPONS)
    # Add other event type details if needed for testing specific scenarios


    try:
        response = requests.post(API_ENDPOINT, json=event)
        if response.status_code == 201:
            print(f"Sent {event_type} event for {SUSPICIOUS_PLAYER_ID} at {current_time_utc}")
        else:
            print(f"Failed to send {event_type} event. Status: {response.status_code}")
            print(f"Response: {response.text}") # Print error response text

    except requests.exceptions.ConnectionError:
        print("Connection Error: Flask server not running?")
        return False # Indicate failure
    return True # Indicate success

if __name__ == "__main__":
    print(f"--- Sending CoD-style test data for suspicious player: {SUSPICIOUS_PLAYER_ID} ---")

    # Send 5 headshots (These count towards total_kills)
    print("\nSending 5 headshot events...")
    success = True
    for _ in range(5):
        if not send_test_event('headshot'):
            success = False
            break
        time.sleep(0.1) # Small delay

    # Send 2 moves (Contributes to total_events for move_ratio)
    if success:
        print("\nSending 2 move events...")
        for _ in range(2):
            if not send_test_event('player_move'):
                success = False
                break
            time.sleep(0.1)

    # Optional: Add other events like reloads or grenade throws if needed for testing ratios
    # if success:
    #     print("\nSending 1 reload event...")
    #     send_test_event('reload')
    #     time.sleep(0.1)

    if success:
        print("\n--- Test data sent successfully ---")
    else:
        print("\n--- Failed to send all test data ---")