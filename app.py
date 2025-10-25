from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

# Initialize the Flask application
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- DATABASE CONFIGURATION ---
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


# --- UPDATED: ML ANALYSIS ENDPOINT (Isolation Forest) ---
@app.route("/api/suspicious-players", methods=['GET'])
def get_suspicious_players():
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
    
    if df.empty or len(df) < 5: # Need some data to model
        return jsonify([]) 
    
    # 1. Feature Engineering:
    #    We will create a feature vector for each player
    #    The features will be the *counts* of each event type
    player_stats = df.groupby('player_id')['event_type'].value_counts().unstack(fill_value=0)
    
    # Get all possible event types as features
    features = player_stats.columns.tolist()

    if not features:
        return jsonify([]) # No features to analyze

    # 2. Train the Model
    #    IsolationForest works well for anomaly detection.
    #    'contamination' is the expected % of anomalies (e.g., 5%)
    #    Adjust 'contamination' based on how many players you want to flag
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(player_stats)
    
    # 3. Get Predictions
    #    The model predicts -1 for anomalies (suspicious) and 1 for inliers (normal)
    predictions = model.predict(player_stats)
    
    # Add predictions to our player_stats DataFrame
    player_stats['is_suspicious'] = predictions
    
    # 4. Filter for suspicious players
    suspicious_players_df = player_stats[player_stats['is_suspicious'] == -1]
    
    # 5. Convert DataFrame to a JSON-friendly format
    suspicious_players_list = []
    for player_id, stats in suspicious_players_df.iterrows():
        # Create a dictionary of the player's event counts
        event_counts = {col: int(stats[col]) for col in features}
        
        suspicious_players_list.append({
            'player_id': player_id,
            'reason': 'Anomaly Detected',
            'event_counts': event_counts
        })
    
    return jsonify(suspicious_players_list)
# --- END OF UPDATED ENDPOINT ---


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

