import requests
import json
from faker import Faker
import random
import time
from datetime import datetime
import pytz

# Initialize Faker
fake = Faker()

# API Endpoint
API_ENDPOINT = "http://127.0.0.1:5000/api/events"

# Expanded Event Types & Weapons for CoD context
COD_EVENT_TYPES = [
    'player_login', 'player_logout', 'player_move', 'kill', 'death',
    'objective_capture', 'reload', 'grenade_throw', 'weapon_pickup', 'headshot'
]

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

OBJECTIVE_TYPES = ['Domination Flag B', 'Hardpoint Hill 3', 'HQ Capture', 'Bomb Plant Site A']
MAPS = ['Shoot House', 'Hackney Yard', 'Crash', 'Shipment']
MODES = ['TDM', 'Domination', 'Hardpoint', 'S&D']

pacific_tz = pytz.timezone('America/Los_Angeles')

def generate_game_event():
    """Generates a single fake Call of Duty style game event."""
    selected_event_type = random.choice(COD_EVENT_TYPES)

    # Use standard YYYY-MM-DDTHH:MM:SSZ format
    current_time_pdt_dt = datetime.now(pacific_tz)
    current_time_pdt = current_time_pdt_dt.isoformat(timespec='seconds')

    # Base event structure
    event = {
        'event_id': fake.uuid4(),
        'player_id': f"player_{random.randint(1000, 9999)}",
        'event_type': selected_event_type,
        'timestamp': current_time_pdt,
        'details': {
            'map': random.choice(MAPS),
            'mode': random.choice(MODES)
        }
    }

    # Add specific details based on event type
    if selected_event_type in ['kill', 'headshot']:
        event['details']['weapon'] = random.choice(COD_WEAPONS)
        event['details']['victim_id'] = f"player_{random.randint(1000, 9999)}"
        while event['details']['victim_id'] == event['player_id']:
            event['details']['victim_id'] = f"player_{random.randint(1000, 9999)}"
        if selected_event_type == 'headshot':
             event['details']['weapon'] = random.choice([w for w in COD_WEAPONS if w not in ['RPG-7', 'Combat Knife', 'Frag Grenade', 'Semtex', 'Throwing Knife']])

    elif selected_event_type == 'death':
        event['details']['killer_id'] = f"player_{random.randint(1000, 9999)}"
        while event['details']['killer_id'] == event['player_id']:
            event['details']['killer_id'] = f"player_{random.randint(1000, 9999)}"
        event['details']['weapon'] = random.choice(COD_WEAPONS)

    elif selected_event_type == 'objective_capture':
        event['details']['objective'] = random.choice(OBJECTIVE_TYPES)

    elif selected_event_type == 'reload':
        event['details']['weapon'] = random.choice([w for w in COD_WEAPONS if w not in ['Combat Knife', 'Frag Grenade', 'Semtex', 'Throwing Knife']])

    elif selected_event_type == 'grenade_throw':
        event['details']['lethal_type'] = random.choice(['Frag Grenade', 'Semtex', 'Throwing Knife'])

    elif selected_event_type == 'weapon_pickup':
        event['details']['weapon'] = random.choice(COD_WEAPONS)
        event['details']['location'] = f"({random.randint(0, 100)}, {random.randint(0, 100)})"

    elif selected_event_type == 'player_move':
         event['details']['location_start'] = f"({random.randint(0, 100)}, {random.randint(0, 100)})"
         event['details']['location_end'] = f"({random.randint(0, 100)}, {random.randint(0, 100)})"

    # Add generic location if none was specific to the event type
    location_keys = ['location', 'location_start']
    if not any(key in event['details'] for key in location_keys):
         event['details']['location'] = f"({random.randint(0, 100)}, {random.randint(0, 100)})"


    return event

def send_event(event):
    """Sends a single event to the API endpoint."""
    try:
        response = requests.post(API_ENDPOINT, json=event)
        if response.status_code == 201:
            print(f"Sent: {event['event_type']} by {event['player_id']} at {event['timestamp']}")
        else:
            print(f"Failed to send event. Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: Could not connect to {API_ENDPOINT}.")

if __name__ == "__main__":
    for i in range(10):
        game_event = generate_game_event()
        send_event(game_event)
        time.sleep(0.1)