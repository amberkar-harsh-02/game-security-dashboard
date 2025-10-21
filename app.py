from flask import Flask

# Initialize the Flask application
app = Flask(__name__)

# Define a route for the root URL ("/")
@app.route("/")
def hello_world():
    return "<p>Hello, World! The server is running!</p>"

# This allows you to run the app directly
if __name__ == '__main__':
    app.run(debug=True)