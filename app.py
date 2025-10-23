from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import pandas as pd  # <-- NEW IMPORT
import numpy as np   # <-- NEW IMPORT

# Initialize the Flask application
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- DATABASE CONFIGURATION ---
# The default username is 'postgres'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Harsh%408866@localhost:8866/game_security'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database extension
db = SQLAlchemy(app)
# --- END DATABASE CONFIGURATION ---


# --- DATABASE MODEL DEFINITION ---
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(50), unique=True, nullable=False)
    player_id = db.Column(db.String(50), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Event {self.event_id}>'
# --- END DATABASE MODEL DEFINITION ---


# --- API ENDPOINTS ---

@app.route("/")
def hello_world():
    return "<p>Hello, World! The server is running!</p>"

@app.route("/api/events", methods=['POST'])
def handle_event():
    event_data = request.get_json()
    if not event_data:
        return jsonify({"error": "Invalid request: No data provided"}), 400
        
    new_event = Event(
        event_id=event_data['event_id'],
        player_id=event_data['player_id'],
        event_type=event_data['event_type'],
        timestamp=event_data['timestamp'],
        details=json.dumps(event_data['details'])
    )
    
    db.session.add(new_event)
    db.session.commit()
    
    print(f"Stored event {new_event.event_id} for player {new_event.player_id}")
    
    return jsonify({"message": f"Event {new_event.event_id} received and stored"}), 201

@app.route("/api/get-events", methods=['GET'])
def get_events():
    events_list = []
    # Query for all events, order by timestamp descending
    events = Event.query.order_by(Event.timestamp.desc()).all()
    
    for event in events:
        events_list.append({
            'event_id': event.event_id,
            'player_id': event.player_id,
            'event_type': event.event_type,
            'timestamp': event.timestamp,
            'details': json.loads(event.details)
        })
        
    return jsonify(events_list)


# --- ML ANALYSIS ENDPOINT ---
@app.route("/api/suspicious-players", methods=['GET'])
def get_suspicious_players():
    # --- This is the logic from ml_analysis.py ---
    events = Event.query.all()
    
    if not events:
        return jsonify([]) # Return empty list if no data

    data = []
    for event in events:
        data.append({
            'player_id': event.player_id,
            'event_type': event.event_type,
        })

    df = pd.DataFrame(data)
    
    if df.empty:
        return jsonify([]) # Return empty list if no data
    
    # 1. Group by player_id and count specific events
    player_stats = df.groupby('player_id')['event_type'].value_counts().unstack(fill_value=0)
    
    # Ensure 'headshot' and 'player_move' columns exist after unstacking
    if 'headshot' not in player_stats.columns:
        player_stats['headshot'] = 0
    if 'player_move' not in player_stats.columns:
        player_stats['player_move'] = 0

    # 2. Engineer our "suspicion" feature
    player_stats['hs_per_move_ratio'] = np.where(
        player_stats['player_move'] > 0, 
        player_stats['headshot'] / player_stats['player_move'],
        0
    )
    
    # 3. Define our "suspicious" threshold
    SUSPICIOUS_THRESHOLD = 1.0
    
    # 4. Filter for suspicious players
    suspicious_players_df = player_stats[
        player_stats['hs_per_move_ratio'] > SUSPICIOUS_THRESHOLD
    ].sort_values(by='hs_per_move_ratio', ascending=False)
    
    # 5. Convert DataFrame to a JSON-friendly format
    suspicious_players_list = []
    for player_id, stats in suspicious_players_df.iterrows():
        suspicious_players_list.append({
            'player_id': player_id,
            'headshots': int(stats['headshot']),
            'moves': int(stats['player_move']),
            'ratio': round(stats['hs_per_move_ratio'], 2)
        })
    # --- End of analysis logic ---
    
    return jsonify(suspicious_players_list)
# --- END OF NEW ENDPOINT ---


if __name__ == '__main__':
    # We must set use_reloader=False because the DB tables
    # are created in the main thread.
    app.run(debug=True, use_reloader=False)
