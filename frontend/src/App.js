import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Define the URL for your Flask API
const API_URL = 'http://127.0.0.1:5000/api/get-events';

function App() {
  // 'events' will hold our list of events from the API
  // 'loading' will be true while we are fetching data
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  // This useEffect hook runs once when the component loads
  useEffect(() => {
    // Define an async function to fetch data
    const fetchEvents = async () => {
      try {
        // Make a GET request to our API
        const response = await axios.get(API_URL);
        // Save the data from the API into our 'events' state
        setEvents(response.data);
      } catch (error) {
        console.error("Error fetching events:", error);
      } finally {
        // Whether it succeeded or failed, we're done loading
        setLoading(false);
      }
    };

    // Call the function
    fetchEvents();
  }, []); // The empty array [] means this effect runs only once

  return (
    <div className="App">
      <header className="App-header">
        <h1>Game Security Dashboard</h1>

        {/* Show a loading message while fetching */}
        {loading ? (
          <p>Loading events...</p>
        ) : (
          /* Once loaded, display the events in a simple table */
          <table>
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Player ID</th>
                <th>Event Type</th>
                <th>Timestamp</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {/* Loop over the events and create a table row for each one */}
              {events.map((event) => (
                <tr key={event.event_id}>
                  <td>{event.event_id}</td>
                  <td>{event.player_id}</td>
                  <td>{event.event_type}</td>
                  <td>{event.timestamp}</td>
                  {/* We use JSON.stringify to display the 'details' object neatly */}
                  <td>{JSON.stringify(event.details)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </header>
    </div>
  );
}

export default App;
