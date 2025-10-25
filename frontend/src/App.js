import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // Correct import path assuming App.css is in the same src directory

// Define the URLs for your Flask API
const EVENTS_API_URL = 'http://127.0.0.1:5000/api/get-events';
const SUSPICIOUS_API_URL = 'http://127.0.0.1:5000/api/suspicious-players';
const REFRESH_INTERVAL = 5000; // 5000ms = 5 seconds

function App() {
  const [events, setEvents] = useState([]);
  const [suspiciousPlayers, setSuspiciousPlayers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filter state variables
  const [filterCategory, setFilterCategory] = useState('player_id'); // What to filter by
  const [filterText, setFilterText] = useState(''); // The search text

  useEffect(() => {
    // Function to fetch data from both endpoints
    const fetchData = async () => {
      // Don't set loading to true on refresh to avoid flickering
      try {
        const [eventsResponse, suspiciousResponse] = await Promise.all([
          axios.get(EVENTS_API_URL),
          axios.get(SUSPICIOUS_API_URL)
        ]);

        setEvents(eventsResponse.data);
        setSuspiciousPlayers(suspiciousResponse.data);

      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        // Set loading to false only on the initial load
        if (loading) {
          setLoading(false);
        }
      }
    };

    fetchData(); // Fetch data immediately on load
    // Set up interval for polling
    const intervalId = setInterval(fetchData, REFRESH_INTERVAL);

    // Cleanup function to clear interval on unmount
    return () => clearInterval(intervalId);
  }, [loading]); // Dependency array includes loading

  // Filter events based on selected category and text
  const filteredEvents = events.filter(event => {
    const filterValue = filterText.toLowerCase();
    let eventValue;

    // Handle searching within the 'details' object
    if (filterCategory === 'details') {
      eventValue = JSON.stringify(event.details).toLowerCase();
    } else {
      // Handle standard string/number columns
      eventValue = (event[filterCategory] || '').toString().toLowerCase();
    }

    return eventValue.includes(filterValue);
  });

  return (
    <div className="App">
      <header className="App-header">
        <h1>Game Security Dashboard</h1>

        {loading ? (
          <p>Loading data...</p>
        ) : (
          <>
            {/* Suspicious Players Table */}
            <div className="table-container">
              <h2>Suspicious Players (Flagged by ML Model)</h2>
              <table>
                <thead>
                  <tr>
                    <th>Player ID</th>
                    <th>Reason</th>
                    <th>Event Counts (as features)</th>
                  </tr>
                </thead>
                <tbody>
                  {suspiciousPlayers.map((player) => (
                    <tr key={player.player_id} className="suspicious-row">
                      <td>{player.player_id}</td>
                      <td>{player.reason}</td>
                      {/* Display the event counts object */}
                      <td>{JSON.stringify(player.event_counts)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {suspiciousPlayers.length === 0 && <p>No suspicious players found.</p>}
            </div>

            {/* Live Event Log Table */}
            <div className="table-container">
              <div className="filter-container">
                <h2>Live Event Log (Auto-Refreshes every 5s)</h2>
                {/* Filter Controls */}
                <div className="filter-controls">
                  <label htmlFor="filter-category" className="filter-label">Filter by:</label>
                  <select
                    id="filter-category"
                    className="filter-select"
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                  >
                    <option value="player_id">Player ID</option>
                    <option value="event_type">Event Type</option>
                    <option value="timestamp">Timestamp</option>
                    <option value="event_id">Event ID</option>
                    <option value="details">Details</option>
                  </select>

                  <input
                    type="text"
                    placeholder="Search value..."
                    className="filter-input"
                    value={filterText}
                    onChange={(e) => setFilterText(e.target.value)}
                  />
                </div>
              </div>

              {/* Event Log Table */}
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
                  {filteredEvents.map((event) => (
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
              {filteredEvents.length === 0 && <p>No events match filter.</p>}
            </div>
          </>
        )}
      </header>
    </div>
  );
}

export default App;