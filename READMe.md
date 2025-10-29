# Game Security & Anomaly Detection Dashboard

## Project Overview

This project is a full-stack web application designed to monitor simulated real-time game event data (inspired by Call of Duty) and identify suspicious player behavior using a machine learning-powered backend. The goal is to build a practical tool demonstrating concepts used by game security and anti-cheat teams.

**Current Status:** ✅ **Core Features Implemented** ✅

## Features

* **Event Ingestion:** Flask backend API receives and stores simulated CoD-style game events (kills, deaths, headshots, moves, reloads, etc.) with real timestamps.
* **Persistent Data Storage:** PostgreSQL database stores event logs.
* **ML-Powered Anomaly Detection:**
    * Backend calculates features per player (KDR, Headshot Ratio, Move Ratio based on total kills/events).
    * Uses Scikit-learn's `IsolationForest` model to identify players with anomalous feature patterns.
    * Provides a basic explanation for why a player was flagged (e.g., "Anomaly: High KDR, Low Move Ratio").
* **Dynamic Security Dashboard (React Frontend):**
    * Displays a list of players flagged as suspicious, showing key performance stats (KDR, HS%, Move%, etc.).
    * Visualizes event frequency over time using a line chart (Recharts), aggregated into 5-minute intervals.
    * Shows a filterable live log of all incoming game events.
    * Includes a Player Drill-Down modal, activated by clicking player IDs, showing detailed stats and recent events for that specific player.
    * Features real-time updates using WebSockets (`Flask-SocketIO` and `socket.io-client`), automatically refreshing data when new events arrive.
    * Includes loading/error indicators for a better user experience.
* **Data Simulation:** Python scripts generate random CoD-style events or specific suspicious patterns for testing.

## Tech Stack Used

* **Frontend:** React.js, Axios, `socket.io-client`, Recharts
* **Backend:** Python, Flask, Flask-SQLAlchemy, `Flask-SocketIO`
* **Machine Learning:** Scikit-learn (`IsolationForest`), Pandas, NumPy
* **Database:** PostgreSQL (`psycopg2-binary`)
* **Web Server (for Flask):** Gunicorn (configured via `Procfile`, though currently run via `socketio.run` for development)

## Running the Project Locally

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Python 3.x
* Node.js and npm
* PostgreSQL (Installed and running)
* Git

### Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <YOUR_GITHUB_REPO_URL.git>
    cd game-security-dashboard
    ```

2.  **Backend Setup:**
    * **Create and activate a Python virtual environment:**
        * *On Windows:*
            ```bash
            python -m venv venv
            # If needed: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
            .\venv\Scripts\activate
            ```
        * *On macOS/Linux:*
            ```bash
            python3 -m venv venv
            source venv/bin/activate
            ```
    * **Install Python dependencies:**
        ```bash
        pip install -r requirements.txt
        ```
    * **Database Setup:**
        * Ensure your PostgreSQL server is running.
        * Create a database named `game_security`.
        * Update the database connection string (`SQLALCHEMY_DATABASE_URI`) in `app.py` with your PostgreSQL username, password, and correct port (if not default 5432). Remember to URL-encode special characters in the password (e.g., `@` becomes `%40`).
        * **Initialize the database tables (Run once):**
            ```bash
            # Start a Python interactive shell in the activated venv
            python
            ```
            ```python
            # Inside the Python shell:
            >>> from app import app, db
            >>> with app.app_context():
            ...     db.create_all()
            ...
            >>> exit()
            ```

3.  **Frontend Setup:**
    * **Navigate to the frontend directory:**
        ```bash
        cd frontend
        ```
    * **Install Node.js dependencies:**
        ```bash
        npm install
        ```
    * **Return to the root project directory:**
        ```bash
        cd ..
        ```

### Running the Application

You need to run the backend and frontend servers simultaneously in separate terminals.

1.  **Terminal 1 (Backend):**
    * Navigate to the project root (`game-security-dashboard`).
    * Activate the Python virtual environment (`.\venv\Scripts\activate` or `source venv/bin/activate`).
    * Run the Flask-SocketIO server:
        ```bash
        python app.py
        ```
    * Keep this terminal running.

2.  **Terminal 2 (Frontend):**
    * Navigate to the `frontend` directory (`cd frontend`).
    * Start the React development server:
        ```bash
        npm start
        ```
    * Keep this terminal running. Your browser should automatically open to `http://localhost:3000`.

3.  **Terminal 3 (Optional - Data Simulation):**
    * Navigate to the project root.
    * Activate the Python virtual environment.
    * Run the simulators to generate data:
        ```bash
        # Generate random CoD-style data
        python data_simulator.py

        # Generate specific suspicious data for player_TEST_BOT_999
        python test_suspicious_player.py
        ```
    * Watch the dashboard update in real-time!

## Future Goals (Optional)

* **Deploy Backend:** Deploy the Flask backend and PostgreSQL database to a cloud hosting service (e.g., Render, Heroku, AWS).
* **Refine ML Model:** Experiment with different `IsolationForest` parameters (like `contamination`) or try alternative anomaly detection models (e.g., `Local Outlier Factor`).
* **Add More Features:** Incorporate additional calculated features (e.g., Objective Score, Kills Per Minute) into the ML model.
* **Enhance UI:** Add date/time filtering, table sorting, or more detailed player drill-down views.
* **User Authentication:** Implement a login system if the dashboard were to be used by multiple analysts.
* **Optimize Performance:** For larger datasets, optimize database queries and backend processing.
