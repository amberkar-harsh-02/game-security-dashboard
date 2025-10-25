from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime, timezone # Keep datetime
import traceback # Keep traceback for error handling

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
    timestamp = db.Column(db.String(50), nullable=False) # Store as ISO string
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

    required_fields = ['event_id', 'player_id', 'event_type', 'timestamp']
    if not all(field in event_data for field in required_fields):
         return jsonify({"error": "Missing required fields"}), 400

    new_event = Event(
        event_id=event_data['event_id'],
        player_id=event_data['player_id'],
        event_type=event_data['event_type'],
        timestamp=event_data['timestamp'],
        details=json.dumps(event_data.get('details', {}))
    )
    try:
        db.session.add(new_event)
        db.session.commit()
        return jsonify({"message": f"Event {new_event.event_id} received and stored"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error storing event: {e}")
        return jsonify({"error": "Database error occurred"}), 500


@app.route("/api/get-events", methods=['GET'])
def get_events():
    events_list = []
    try:
        events = Event.query.order_by(db.desc(Event.timestamp)).all()
        for event in events:
            details_dict = {}
            try:
                details_dict = json.loads(event.details) if event.details else {}
            except json.JSONDecodeError:
                details_dict = {"error": "invalid format"}

            events_list.append({
                'event_id': event.event_id,
                'player_id': event.player_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp,
                'details': details_dict
            })
        return jsonify(events_list)
    except Exception as e:
        print(f"Error fetching events: {e}")
        return jsonify({"error": "Failed to fetch events"}), 500


# --- TUNED ISOLATION FOREST ENDPOINT ---
@app.route("/api/suspicious-players", methods=['GET'])
def get_suspicious_players():
    try:
        events = Event.query.all()
        if not events: return jsonify([])

        data = [{'player_id': e.player_id, 'event_type': e.event_type} for e in events]
        df = pd.DataFrame(data)
        if df.empty: return jsonify([])

        player_stats = df.groupby('player_id')['event_type'].value_counts().unstack(fill_value=0)

        all_event_types = ['player_login', 'player_logout', 'player_move', 'item_pickup', 'headshot']
        for event_type in all_event_types:
            if event_type not in player_stats.columns:
                player_stats[event_type] = 0

        features = player_stats[all_event_types]

        if len(features) < 2:
            return jsonify([])

        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(features)
        predictions = model.predict(features)

        suspicious_mask = (predictions == -1)
        suspicious_players_df = player_stats[suspicious_mask]

        suspicious_players_list = []
        for player_id, stats in suspicious_players_df.iterrows():
            event_counts_data = {etype: int(stats.get(etype, 0)) for etype in all_event_types}
            suspicious_players_list.append({
                'player_id': player_id,
                'reason': 'Anomalous behavior detected by Isolation Forest model',
                'event_counts': event_counts_data
            })

        suspicious_players_list.sort(key=lambda p: p['event_counts'].get('headshot', 0), reverse=True)
        return jsonify(suspicious_players_list)

    except Exception as e:
        print(f"Error during anomaly detection: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed during ML prediction: {e}"}), 500
# --- END ISOLATION FOREST ENDPOINT ---


# --- FINAL EVENT SUMMARY ENDPOINT (Auto-detect Timestamp Format) ---
@app.route("/api/event-summary", methods=['GET'])
def get_event_summary():
    # print("\n--- Request received for /api/event-summary ---") # Debugging removed
    try:
        events = Event.query.all() # Fetch ALL events
        if not events:
            # print("DEBUG (Summary): No events found in database.") # Debugging removed
            return jsonify([])

        data = [{'timestamp': event.timestamp, 'event_type': event.event_type} for event in events]
        df = pd.DataFrame(data)
        if df.empty:
            return jsonify([])

        # --- Revert to Auto-Detect Format ---
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        # --- End Revert ---

        df = df.dropna(subset=['timestamp']) # Drop rows where conversion failed
        if df.empty:
            return jsonify([])

        # Set index for resampling
        df = df.set_index('timestamp')

        # Aggregate by 15-minute intervals (Adjust freq if needed)
        summary = df.groupby(pd.Grouper(freq='15min'))['event_type'].value_counts().unstack(fill_value=0)
        if summary.empty:
             return jsonify([])

        summary = summary.reset_index()

        # Format timestamp for display
        summary['timestamp'] = summary['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

        # Ensure all expected event types exist as columns
        all_event_types = ['player_login', 'player_logout', 'player_move', 'item_pickup', 'headshot']
        for event_type in all_event_types:
            if event_type not in summary.columns:
                summary[event_type] = 0

        summary = summary[['timestamp'] + all_event_types]

        chart_data = summary.to_dict(orient='records')

        return jsonify(chart_data)

    except Exception as e:
        print(f"ERROR processing event summary: {e}") # Use ERROR for exceptions
        print(traceback.format_exc()) # Print full traceback for errors
        return jsonify({"error": f"Failed to generate summary: {e}"}), 500

if __name__ == '__main__':
    # Use standard app.run
    app.run(debug=True, use_reloader=False)