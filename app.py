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


# --- ML ANALYSIS ENDPOINT (Corrected Kill Logic) ---
@app.route("/api/suspicious-players", methods=['GET'])
def get_suspicious_players():
    # print("\n--- Request received for /api/suspicious-players ---") # Optional Debug
    try:
        events = Event.query.all()
        if not events: return jsonify([])

        data = [{'player_id': e.player_id, 'event_type': e.event_type} for e in events]
        df = pd.DataFrame(data)
        if df.empty: return jsonify([])

        # 1. Aggregate Raw Counts
        player_stats = df.groupby('player_id')['event_type'].value_counts().unstack(fill_value=0)

        # Ensure essential columns for calculation exist
        for col in ['kill', 'death', 'headshot']:
            if col not in player_stats.columns:
                player_stats[col] = 0

        # --- 2. Feature Engineering (Corrected Logic) ---
        # Calculate Total Kills = 'kill' events + 'headshot' events
        player_stats['total_kills'] = player_stats['kill'] + player_stats['headshot']

        # Calculate KDR using total_kills (handle division by zero)
        player_stats['kdr'] = np.where(
            player_stats['death'] > 0,
            player_stats['total_kills'] / player_stats['death'],
            player_stats['total_kills'] # Assign total kills if deaths are 0
        )
        # Calculate Headshot Ratio using total_kills (handle division by zero)
        player_stats['hs_ratio'] = np.where(
            player_stats['total_kills'] > 0,
            player_stats['headshot'] / player_stats['total_kills'],
            0 # Assign 0 if total_kills are 0
        )
        # --- End Corrected Feature Engineering ---

        # 3. Select Features for the Model
        # Use the new calculated ratios and total kills
        feature_columns = ['kdr', 'hs_ratio', 'total_kills', 'death'] # Add other raw counts if desired
        # Make sure all feature columns exist in player_stats before selection
        for col in feature_columns:
            if col not in player_stats.columns:
                player_stats[col] = 0 # Should already exist due to logic above, but safer
        features_df = player_stats[feature_columns]

        # Clean up potential NaN/inf values
        features_df = features_df.fillna(0)
        # Replace infinite KDR (if total_kills > 0 and deaths = 0) with total_kills
        features_df.loc[features_df['kdr'] == np.inf, 'kdr'] = features_df.loc[features_df['kdr'] == np.inf, 'total_kills']


        if len(features_df) < 2:
            return jsonify([]) # Model needs at least 2 samples

        # 4. Train Isolation Forest Model
        model = IsolationForest(contamination=0.05, random_state=42) # Adjust contamination if needed
        model.fit(features_df)
        predictions = model.predict(features_df)
        # print(f"DEBUG (Suspicious): Predictions array: {predictions}") # Optional Debug

        # 5. Filter for Anomalies
        suspicious_mask = (predictions == -1)
        suspicious_player_ids = features_df[suspicious_mask].index # Get IDs from the features DF index

        # 6. Format Output
        suspicious_players_list = []
        for player_id in suspicious_player_ids:
            # Get the stats for this player from the features dataframe
            stats = features_df.loc[player_id]
            # Also get the raw headshot count from player_stats for display
            raw_headshots = int(player_stats.loc[player_id, 'headshot'])

            suspicious_players_list.append({
                'player_id': player_id,
                'reason': 'Anomalous KDR/HS Ratio detected by Isolation Forest model',
                'stats': {
                    'kdr': round(stats['kdr'], 2),
                    'hs_ratio': round(stats['hs_ratio'] * 100, 1), # As percentage
                    'total_kills': int(stats['total_kills']), # Send total kills
                    'deaths': int(stats['death']),
                    'headshots': raw_headshots # Send raw headshot count
                }
            })

        # Sort by KDR or HS Ratio for better presentation
        suspicious_players_list.sort(key=lambda p: p['stats']['kdr'], reverse=True)
        # print(f"DEBUG (Suspicious): Final list length: {len(suspicious_players_list)}") # Optional Debug
        return jsonify(suspicious_players_list)

    except Exception as e:
        print(f"Error during anomaly detection: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed during ML prediction: {e}"}), 500
# --- END ISOLATION FOREST ENDPOINT ---


# --- EVENT SUMMARY ENDPOINT (No changes needed here) ---
@app.route("/api/event-summary", methods=['GET'])
def get_event_summary():
    try:
        events = Event.query.all()
        if not events: return jsonify([])
        data = [{'timestamp': event.timestamp, 'event_type': event.event_type} for event in events]
        df = pd.DataFrame(data)
        if df.empty: return jsonify([])

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        df = df.dropna(subset=['timestamp'])
        if df.empty: return jsonify([])

        df = df.set_index('timestamp')
        summary = df.groupby(pd.Grouper(freq='5min'))['event_type'].value_counts().unstack(fill_value=0)

        if summary.empty: return jsonify([])
        summary = summary.reset_index()
        summary['timestamp'] = summary['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

        all_event_types = [
            'player_login', 'player_logout', 'player_move', 'kill', 'death',
            'objective_capture', 'reload', 'grenade_throw', 'weapon_pickup', 'headshot'
        ]
        for event_type in all_event_types:
            if event_type not in summary.columns:
                summary[event_type] = 0
        summary = summary[['timestamp'] + all_event_types]

        chart_data = summary.to_dict(orient='records')
        return jsonify(chart_data)

    except Exception as e:
        print(f"ERROR processing event summary: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed to generate summary: {e}"}), 500
# --- END EVENT SUMMARY ---

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)