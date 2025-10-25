from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import pandas as pd
import numpy as np
# --- RE-INTRODUCE SCIKIT-LEARN IMPORTS ---
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
# --- END IMPORTS ---

# Initialize the Flask application
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- DATABASE CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Harsh%408866@localhost:8866/game_security'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

# --- (handle_event and get_events remain the same) ---
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
# --- END (handle_event and get_events) ---


# --- UPDATED: TUNED ISOLATION FOREST ENDPOINT ---
@app.route("/api/suspicious-players", methods=['GET'])
def get_suspicious_players():
    events = Event.query.all()
    if not events:
        return jsonify([])

    # Use only player_id and event_type for initial aggregation
    data = [{'player_id': e.player_id, 'event_type': e.event_type} for e in events]
    df = pd.DataFrame(data)
    if df.empty:
        return jsonify([])

    # 1. Feature Engineering: Count all event types per player
    player_stats = df.groupby('player_id')['event_type'].value_counts().unstack(fill_value=0)

    # Define all possible event types we care about as features
    all_event_types = ['player_login', 'player_logout', 'player_move', 'item_pickup', 'headshot']
    # Ensure all columns exist, adding them with 0 if they don't
    for event_type in all_event_types:
        if event_type not in player_stats.columns:
            player_stats[event_type] = 0

    # Select only the feature columns for the model
    features = player_stats[all_event_types]

    # Handle case with too few samples for Isolation Forest
    if len(features) < 2:
         print("Not enough player data (need at least 2 players) for Isolation Forest.")
         return jsonify([])

    # --- ISOLATION FOREST MODEL ---
    try:
        # 2. Preprocessing (Optional but recommended: Scale features)
        # scaler = StandardScaler()
        # scaled_features = scaler.fit_transform(features)
        # Using raw counts might be fine here, let's try without scaling first.

        # 3. Initialize and Fit Model with low contamination
        # Adjust contamination: lower value means stricter anomaly detection (fewer anomalies)
        # Try 0.05 (5%) or 0.01 (1%) instead of 'auto'
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(features)

        # 4. Predict Anomalies (-1 for anomalies, 1 for inliers)
        predictions = model.predict(features)

        # 5. Filter for anomalies
        suspicious_mask = (predictions == -1)
        suspicious_players_df = player_stats[suspicious_mask]

    except Exception as e:
        print(f"Error during Isolation Forest prediction: {e}")
        return jsonify({"error": f"Failed during ML prediction: {e}"}), 500
    # --- END MODEL ---

    # 6. Format results for JSON output
    suspicious_players_list = []
    for player_id, stats in suspicious_players_df.iterrows():
        # Get the full event counts for context
        event_counts_data = {etype: int(stats.get(etype, 0)) for etype in all_event_types}

        suspicious_players_list.append({
            'player_id': player_id,
            'reason': 'Anomalous behavior detected by Isolation Forest model', # Generic reason
            'event_counts': event_counts_data
        })

    # Optional: Sort by headshot count for easier viewing, even though model didn't use it directly for filtering
    suspicious_players_list.sort(key=lambda p: p['event_counts'].get('headshot', 0), reverse=True)

    return jsonify(suspicious_players_list)
# --- END UPDATED ENDPOINT ---


# --- EVENT SUMMARY ENDPOINT (No Changes Needed) ---
@app.route("/api/event-summary", methods=['GET'])
def get_event_summary():
    events = Event.query.all()
    if not events: return jsonify([])
    data = [{'timestamp': e.timestamp, 'event_type': e.event_type} for e in events]
    df = pd.DataFrame(data)
    if df.empty: return jsonify([])

    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        if df.empty: return jsonify([])
        df = df.set_index('timestamp')
        summary = df.groupby(pd.Grouper(freq='H'))['event_type'].value_counts().unstack(fill_value=0)
        summary = summary.reset_index()
        summary['timestamp'] = summary['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        all_event_types = ['player_login', 'player_logout', 'player_move', 'item_pickup', 'headshot']
        for event_type in all_event_types:
            if event_type not in summary.columns: summary[event_type] = 0
        summary = summary[['timestamp'] + all_event_types]
        chart_data = summary.to_dict(orient='records')
        return jsonify(chart_data)
    except Exception as e:
        print(f"Error processing event summary: {e}")
        return jsonify({"error": f"Failed to generate summary: {e}"}), 500
# --- END EVENT SUMMARY ---

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)