import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Define the URLs for your Flask API
const EVENTS_API_URL = 'http://127.0.0.1:5000/api/get-events';
const SUSPICIOUS_API_URL = 'http://127.0.0.1:5000/api/suspicious-players';
const REFRESH_INTERVAL = 5000; // 5000ms = 5 seconds

function App() {
  const [events, setEvents] = useState([]);
  const [suspiciousPlayers, setSuspiciousPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // --- NEW FILTER STATE ---
  // We now have two states for filtering
  const [filterCategory, setFilterCategory] = useState('player_id'); // What to filter by
  const [filterText, setFilterText] = useState(''); // The search text
  // --- END NEW FILTER STATE ---

  useEffect(() => {
    const fetchData = async () => {
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
        if (loading) {
          setLoading(false);
        }
      }
    };

    fetchData(); // Fetch data immediately on load
    const intervalId = setInterval(fetchData, REFRESH_INTERVAL); // Set up the 5-second poll
    return () => clearInterval(intervalId); // Cleanup
  }, [loading]); // Dependency array

  // --- NEW DYNAMIC FILTER LOGIC ---
  const filteredEvents = events.filter(event => {
    const filterValue = filterText.toLowerCase();
    
    // Get the value from the event based on the selected category
    let eventValue;
    if (filterCategory === 'details') {
      // Special case: stringify the 'details' object to make it searchable
      eventValue = JSON.stringify(event.details).toLowerCase();
    } else {
      // Standard cases: player_id, event_type, etc.
      // Use .toString() to safely handle any data type
      eventValue = (event[filterCategory] || '').toString().toLowerCase();
    }
    
    // Return true if the event value includes the filter text
    return eventValue.includes(filterValue);
  });
  // --- END NEW DYNAMIC FILTER LOGIC ---

  return (
    <div className="App">
      <header className="App-header">
        <h1>Game Security Dashboard</h1>
        
        {loading ? (
          <p>Loading data...</p>
        ) : (
          <>
            <div className="table-container">
              <h2>Suspicious Players (Auto-Refreshes every 5s)</h2>
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
              
              {/* --- NEW FILTER CONTROLS --- */}
              <div className="filter-container">
                <h2>Live Event Log (Auto-Refreshes every 5s)</h2>
                
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
              {/* --- END FILTER CONTROLS --- */}
              
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