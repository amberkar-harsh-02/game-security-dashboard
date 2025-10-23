import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Define the URLs for your Flask API
const EVENTS_API_URL = 'http://127.0.0.1:5000/api/get-events';
const SUSPICIOUS_API_URL = 'http://127.0.0.1:5000/api/suspicious-players';

function App() {
  const [events, setEvents] = useState([]);
  const [suspiciousPlayers, setSuspiciousPlayers] = useState([]); // <-- NEW STATE
  const [loading, setLoading] = useState(true);

  // This useEffect hook runs once when the component loads
  useEffect(() => {
    // We create one function to fetch all our data
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch both sets of data in parallel
        const [eventsResponse, suspiciousResponse] = await Promise.all([
          axios.get(EVENTS_API_URL),
          axios.get(SUSPICIOUS_API_URL) // <-- NEW FETCH CALL
        ]);
        
        setEvents(eventsResponse.data);
        setSuspiciousPlayers(suspiciousResponse.data); // <-- SAVE NEW DATA

      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []); // The empty array [] means this effect runs only once

  return (
    <div className="App">
      <header className="App-header">
        <h1>Game Security Dashboard</h1>
        
        {loading ? (
          <p>Loading data...</p>
        ) : (
          // Use React Fragments <> to return multiple elements
          <>
            {/* --- NEW SUSPICIOUS PLAYERS TABLE --- */}
            <div className="table-container">
              <h2>Suspicious Players (Headshot/Move Ratio {'>'} 1.0)</h2>
              <table>
                <thead>
                  <tr>
                    <th>Player ID</th>
                    <th>Headshots</th>
                    <th>Moves</th>
                    <th>HS/Move Ratio</th>
                  </tr>
                </thead>
                <tbody>
                  {suspiciousPlayers.map((player) => (
                    <tr key={player.player_id} className="suspicious-row">
                      <td>{player.player_id}</td>
                      <td>{player.headshots}</td>
                      <td>{player.moves}</td>
                      <td>{player.ratio}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {suspiciousPlayers.length === 0 && <p>No suspicious players found.</p>}
            </div>

            {/* --- EXISTING EVENT LOG TABLE --- */}
            <div className="table-container">
              <h2>Live Event Log (Latest First)</h2>
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
                  {events.map((event) => (
                    <tr key={event.event_id}>
                      <td>{event.event_id}</td>
                      <td>{event.player_id}</td>
                      <td>{event.event_type}</td>
                      <td>{event.timestamp}</td>
                      <td>{JSON.stringify(event.details)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </header>
    </div>
  );
}

export default App;
