from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- DATABASE CONFIGURATION ---
# The default username is 'postgres'
# Replace 'YOUR_PASSWORD_HERE' with the password you created during installation
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Harsh%408866@localhost:8866/game_security'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database extension
db = SQLAlchemy(app)
# --- END DATABASE CONFIGURATION ---


# --- DATABASE MODEL DEFINITION ---
# This class defines the structure of our 'events' table in the database
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Auto-incrementing primary key
    event_id = db.Column(db.String(50), unique=True, nullable=False)
    player_id = db.Column(db.String(50), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    
    # We will store the 'details' JSON object as a string
    details = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Event {self.event_id}>'
# --- END DATABASE MODEL DEFINITION ---


@app.route("/")
def hello_world():
    return "<p>Hello, World! The server is running!</p>"

# MODIFIED: This route now saves events to the database
@app.route("/api/events", methods=['POST'])
def handle_event():
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid request: No data provided"}), 400
        
    # Create a new Event object using our model
    new_event = Event(
        event_id=event_data['event_id'],
        player_id=event_data['player_id'],
        event_type=event_data['event_type'],
        timestamp=event_data['timestamp'],
        details=json.dumps(event_data['details']) # Convert details dict to a JSON string
    )
    
    # Add the new event to the database session and commit it
    db.session.add(new_event)
    db.session.commit()
    
    print(f"Stored event {new_event.event_id} for player {new_event.player_id}")
    
    return jsonify({"message": f"Event {new_event.event_id} received and stored"}), 201

# NEW: This route lets you view all stored events
@app.route("/api/get-events", methods=['GET'])
def get_events():
    events_list = []
    events = Event.query.all() # Query the database for all events
    
    for event in events:
        events_list.append({
            'event_id': event.event_id,
            'player_id': event.player_id,
            'event_type': event.event_type,
            'timestamp': event.timestamp,
            'details': json.loads(event.details) # Convert details string back to dict
        })
        
    return jsonify(events_list)

if __name__ == '__main__':
    app.run(debug=True)