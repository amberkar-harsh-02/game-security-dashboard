from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime, timezone, timedelta # Import timedelta
import traceback

# Initialize Flask app and extensions
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*") # Keep SocketIO if using WebSockets

# --- DATABASE CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Harsh%408866@localhost:8866/game_security'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# --- END DATABASE CONFIGURATION ---
db = SQLAlchemy(app)

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
    # ... (validation and DB storage logic - unchanged) ...
    if not event_data: return jsonify({"error": "Invalid request: No data provided"}), 400
    required_fields = ['event_id', 'player_id', 'event_type', 'timestamp']
    if not all(field in event_data for field in required_fields): return jsonify({"error": "Missing required fields"}), 400

    new_event = Event(
        event_id=event_data['event_id'], player_id=event_data['player_id'],
        event_type=event_data['event_type'], timestamp=event_data['timestamp'],
        details=json.dumps(event_data.get('details', {}))
    )
    try:
        db.session.add(new_event)
        db.session.commit()
        # Emit WebSocket event if using SocketIO
        socketio.emit('new_event', {'data': 'update'})
        # print(f"Stored event {new_event.event_id} and emitted 'new_event'")
        return jsonify({"message": f"Event {new_event.event_id} received and stored"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error storing event: {e}")
        return jsonify({"error": "Database error occurred"}), 500


@app.route("/api/get-events", methods=['GET'])
def get_events():
    # ... (code remains the same) ...
    events_list = []
    try:
        events = Event.query.order_by(db.desc(Event.timestamp)).all()
        for event in events:
            details_dict = {}
            try: details_dict = json.loads(event.details) if event.details else {}
            except json.JSONDecodeError: details_dict = {"error": "invalid format"}
            events_list.append({
                'event_id': event.event_id, 'player_id': event.player_id,
                'event_type': event.event_type, 'timestamp': event.timestamp,
                'details': details_dict
            })
        return jsonify(events_list)
    except Exception as e:
        print(f"Error fetching events: {e}")
        return jsonify({"error": "Failed to fetch events"}), 500


# --- ML ANALYSIS ENDPOINT (Add Minimum Kill Filter) ---
@app.route("/api/suspicious-players", methods=['GET'])
def get_suspicious_players():
    try:
        events = Event.query.all()
        if not events: return jsonify([])

        data = [{'player_id': e.player_id, 'event_type': e.event_type, 'timestamp': e.timestamp} for e in events]
        df = pd.DataFrame(data)
        if df.empty: return jsonify([])

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
        df = df.dropna(subset=['timestamp'])
        if df.empty: return jsonify([])

        # 1. Aggregate Raw Counts
        player_stats = df.groupby('player_id')['event_type'].value_counts().unstack(fill_value=0)

        required_cols = ['kill', 'death', 'headshot', 'reload', 'grenade_throw', 'player_move']
        for col in required_cols:
            if col not in player_stats.columns: player_stats[col] = 0

        # 2. Feature Engineering (Includes KPM)
        player_stats['total_kills'] = player_stats['kill'] + player_stats['headshot']
        player_stats['total_events'] = player_stats.sum(axis=1)

        player_stats['kdr'] = np.where(player_stats['death'] > 0, player_stats['total_kills'] / player_stats['death'], player_stats['total_kills'])
        player_stats['hs_ratio'] = np.where(player_stats['total_kills'] > 0, player_stats['headshot'] / player_stats['total_kills'], 0)
        player_stats['move_ratio'] = np.where(player_stats['total_events'] > 0, player_stats['player_move'] / player_stats['total_events'], 0)

        session_times = df.groupby('player_id')['timestamp'].agg(['min', 'max'])
        session_times['duration_seconds'] = (session_times['max'] - session_times['min']).dt.total_seconds()
        session_times['duration_minutes'] = session_times['duration_seconds'].apply(lambda x: max(x / 60, 1.0))
        player_stats = player_stats.join(session_times[['duration_minutes']])
        player_stats['duration_minutes'].fillna(1.0, inplace=True)
        player_stats['kpm'] = player_stats['total_kills'] / player_stats['duration_minutes']

        # 3. Select Features for the Model
        feature_columns = ['kdr', 'hs_ratio', 'move_ratio', 'kpm', 'total_kills']
        for col in feature_columns:
            if col not in player_stats.columns: player_stats[col] = 0
        features_df = player_stats[feature_columns].copy()

        features_df.fillna(0, inplace=True)
        features_df.loc[features_df['kdr'] == np.inf, 'kdr'] = features_df.loc[features_df['kdr'] == np.inf, 'total_kills'] * 2
        features_df.loc[features_df['move_ratio'] == np.inf, 'move_ratio'] = 0
        features_df.loc[features_df['kpm'] == np.inf, 'kpm'] = features_df.loc[features_df['kpm'] == np.inf, 'total_kills']

        if len(features_df) < 2: return jsonify([])

        # 4. Train Isolation Forest Model
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(features_df)
        predictions = model.predict(features_df)

        # 5. Filter for Anomalies Identified by Model
        suspicious_mask = (predictions == -1)
        suspicious_player_ids_ml = features_df[suspicious_mask].index # IDs flagged by ML

        # --- 6. NEW: Apply Minimum Kill Threshold ---
        MINIMUM_KILLS_THRESHOLD = 5 # Set your desired threshold here
        suspicious_players_list = []
        # Iterate through players flagged by ML
        for player_id in suspicious_player_ids_ml:
            # Check if this player meets the minimum kill count
            if player_stats.loc[player_id, 'total_kills'] > MINIMUM_KILLS_THRESHOLD:
                # Player is flagged by ML AND has enough kills - add them to the final list
                stats = features_df.loc[player_id]
                raw_counts = player_stats.loc[player_id]

                # Basic Explainability Logic (remains the same)
                median_stats = features_df.median()
                kdr_threshold_high = median_stats['kdr'] * 2 + 1
                hs_ratio_threshold_high = median_stats['hs_ratio'] * 2 + 0.1
                move_ratio_threshold_low = median_stats['move_ratio'] * 0.5
                kpm_threshold_high = median_stats['kpm'] * 2 + 0.5

                reasons = []
                if stats['kdr'] > kdr_threshold_high: reasons.append("High KDR")
                if stats['hs_ratio'] > hs_ratio_threshold_high: reasons.append("High HS Ratio")
                if stats['kpm'] > kpm_threshold_high: reasons.append("High KPM")
                if stats['move_ratio'] < move_ratio_threshold_low and raw_counts['total_events'] > 5: reasons.append("Low Move Ratio")

                reason_str = f"Anomaly: {', '.join(reasons)}" if reasons else "Anomaly detected (General)"

                suspicious_players_list.append({
                    'player_id': player_id,
                    'reason': reason_str,
                    'stats': {
                        'kdr': round(stats['kdr'], 2),
                        'hs_ratio': round(stats['hs_ratio'] * 100, 1), # %
                        'move_ratio': round(stats['move_ratio'] * 100, 1), # %
                        'kpm': round(stats['kpm'], 2),
                        'total_kills': int(raw_counts['total_kills']),
                        'deaths': int(raw_counts['death']),
                        'headshots': int(raw_counts['headshot']),
                        'moves': int(raw_counts['player_move']),
                        'total_events': int(raw_counts['total_events']),
                        'session_minutes': round(raw_counts['duration_minutes'], 1)
                    }
                })
        # --- END NEW FILTER ---

        # 7. Sort Final List
        suspicious_players_list.sort(key=lambda p: p['stats']['kdr'], reverse=True)
        return jsonify(suspicious_players_list)

    except Exception as e:
        print(f"Error during anomaly detection: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed during ML prediction: {e}"}), 500
# --- END ISOLATION FOREST ENDPOINT ---


# --- EVENT SUMMARY ENDPOINT (No changes needed) ---
@app.route("/api/event-summary", methods=['GET'])
def get_event_summary():
    # ... (code remains the same) ...
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
            if event_type not in summary.columns: summary[event_type] = 0
        summary = summary[['timestamp'] + all_event_types]

        chart_data = summary.to_dict(orient='records')
        return jsonify(chart_data)

    except Exception as e:
        print(f"ERROR processing event summary: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed to generate summary: {e}"}), 500


# --- SocketIO Handlers ---
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)