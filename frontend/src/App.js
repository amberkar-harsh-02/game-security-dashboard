import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Define the URLs for your Flask API
const EVENTS_API_URL = 'http://127.0.0.1:5000/api/get-events';
const SUSPICIOUS_API_URL = 'http://127.0.0.1:5000/api/suspicious-players';
const REFRESH_INTERVAL = 2000; // 5000ms = 5 seconds

function App() {
  const [events, setEvents] = useState([]);
  const [suspiciousPlayers, setSuspiciousPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(''); // <-- NEW STATE for the filter

  // This useEffect hook now handles polling
  useEffect(() => {
    // We create one function to fetch all our data
    const fetchData = async () => {
      // We don't set loading to true here, to avoid screen flashing on refresh
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
        // Only set loading to false on the *first* load
        if (loading) {
          setLoading(false);
        }
      }
    };

    // --- NEW POLLING LOGIC ---
    fetchData(); // Fetch data immediately on component load

    // Set up an interval to re-fetch data every 5 seconds
    const intervalId = setInterval(fetchData, REFRESH_INTERVAL);

    // This is a cleanup function
    // React runs this when the component is "unmounted" (e.g., page is closed)
    // This prevents memory leaks by stopping the interval
    return () => clearInterval(intervalId);
    // --- END NEW POLLING LOGIC ---

  }, [loading]); // We add 'loading' as a dependency

  // --- NEW: Client-side filtering ---
  // We create a new array of filtered events based on the 'filter' state
  const filteredEvents = events.filter(event => 
    event.player_id.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="App">
      <header className="App-header">
        <h1>Game Security Dashboard</h1>
        
        {loading ? (
          <p>Loading data...</p>
        ) : (
          <>
            <div className="table-container">
              <h2>Suspicious Players (Auto-Refreshes every 2s)</h2>
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

            <div className="table-container">
              {/* --- NEW FILTER INPUT BOX --- */}
              <div className="filter-container">
                <h2>Live Event Log (Auto-Refreshes every 5s)</h2>
                <input 
                  type="text"
                  placeholder="Filter by Player ID..."
                  className="filter-input"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                />
              </div>
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
                  {/* --- MODIFIED: We now map over 'filteredEvents' --- */}
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