# **Game Security & Anomaly Detection Dashboard**

## **Project Overview**

This project is a full-stack web application designed to monitor real-time game event data and identify suspicious player behavior using a machine learning-powered backend. The goal is to build a practical tool that reflects the challenges faced by game security and anti-cheat teams in the live-service gaming industry.

This project is being developed as part of a focused effort to build skills relevant to security and anti-cheat roles at companies like Activision Blizzard.

**Current Status:** 🚧 **In Early Development** 🚧

## **Planned Features**

* **Real-Time Event Ingestion:** A Flask-based REST API to receive and process simulated game event data (e.g., player actions, positions, login attempts).  
* **ML-Powered Anomaly Detection:** A Python backend service using Scikit-learn to analyze player behavior and flag potential cheating or security threats.  
* **Dynamic Security Dashboard:** A React frontend that visualizes incoming events, displays security alerts, and provides an overview of game integrity.  
* **Persistent Data Storage:** A robust database (PostgreSQL) to store event logs and player threat profiles for historical analysis.  
* **Cloud Deployment:** The entire application will be deployed on AWS to demonstrate scalable and secure cloud architecture practices.

## **Planned Tech Stack**

* **Frontend:** React.js  
* **Backend:** Python, Flask  
* **Machine Learning:** Scikit-learn, Pandas  
* **Database:** PostgreSQL  
* **Deployment:** AWS (EC2, RDS)

## **Running the Project Locally**

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### **Prerequisites**

* Python 3.x  
* Git

### **Setup and Installation**

1. **Clone the repository:**  
   git clone \<YOUR\_GITHUB\_REPO\_URL.git\>  
   cd game-security-dashboard

2. **Create and activate a Python virtual environment:**  
   *On Windows:*  
   python \-m venv venv  
   \# If you get an error about script execution being disabled, run this command first:  
   \# Set-ExecutionPolicy \-ExecutionPolicy RemoteSigned \-Scope Process  
   .\\venv\\Scripts\\activate

   *On macOS/Linux:*  
   python3 \-m venv venv  
   source venv/bin/activate

3. **Install the required dependencies:**  
   pip install Flask

4. **Run the Flask development server:**  
   python app.py

5. View the application:  
   Open your browser and navigate to http://12.0.0.1:5000. You should see a confirmation that the server is running.