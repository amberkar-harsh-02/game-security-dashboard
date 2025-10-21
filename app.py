from flask import Flask, request, jsonify
import json

# Initialize the Flask application
app = Flask(__name__)

# Keep the original "Hello, World!" route
@app.route("/")
def hello_world():
    return "<p>Hello, World! The server is running!</p>"

# NEW: Add a route to handle game events
@app.route("/api/events", methods=['POST'])
def handle_event():
    # Get the JSON data sent from the client
    event_data = request.get_json()
    
    if not event_data:
        # Return an error if no JSON was sent
        return jsonify({"error": "Invalid request: No data provided"}), 400
        
    # For now, just print the received data to the server's console
    print("Received event:")
    print(json.dumps(event_data, indent=2))
    
    # Send back a success response
    # The 201 status code means "Created"
    return jsonify({"message": "Event received successfully"}), 201

# This allows you to run the app directly
if __name__ == '__main__':
    # Use debug=True for development
    app.run(debug=True)