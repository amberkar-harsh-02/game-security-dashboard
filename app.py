from flask import Flask

# Initialize the Flask application
app = Flask(__name__)

# Define a route for the root URL ("/")
@app.route("/")
def hello_world():
    return "<h1>Hello, World! The server is running!</h1>"

# This allows you to run the app directly
if __name__ == '__main__':
    app.run(debug=True)