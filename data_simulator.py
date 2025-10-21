import requests
import json
import random
import time
from faker import Faker

fake = Faker()

API_ENDPOINT = "http://127.0.0.1:5000/api/events" #Replace with your actual API endpoint

def generate_game_event():
    """Generates a single fake game event."""
    event_types = ['player_login', 'player_logout', 'player_move', 'item_pickup', 'headshot']
    
    # Create a dictionary representing the event
    event = {
        'event_id': fake.uuid4(),
        'player_id': f"player_{random.randint(1000, 9999)}",
        'event_type': random.choice(event_types),
        'timestamp': fake.iso8601(),
        'details': {
            'location': f"({random.randint(0, 100)}, {random.randint(0, 100)})",
            'weapon': random.choice(['pistol', 'rifle', 'sniper']) if 'headshot' in event_types else None
        }
    }
    return event

def send_event(event):
    """Sends a single event to the API endpoint."""
    try:
        # Send the event as a POST request with JSON data
        response = requests.post(API_ENDPOINT, json=event)
        
        # Check the server's response
        if response.status_code == 201:
            print(f"Successfully sent event: {event['event_id']}")
        else:
            print(f"Failed to send event. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: Could not connect to the server at {API_ENDPOINT}.")
        print("Please ensure the Flask server (app.py) is running.")

if __name__ == "__main__":
    game_event = generate_game_event()
    send_event(game_event)