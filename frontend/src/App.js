import React, { useState, useEffect } from 'react';
import axios from 'axios';
// Import Recharts components
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css'; // Corrected import path for CSS

// Define the URLs for your Flask API
// --- IMPORTANT: Double-check this IP address. If your Flask server is on the same machine, it should be 127.0.0.1 ---
const EVENTS_API_URL = 'http://127.0.0.1:5000/api/get-events';
const SUSPICIOUS_API_URL = 'http://127.0.0.1:5000/api/suspicious-players';
const SUMMARY_API_URL = 'http://127.0.0.1:5000/api/event-summary';
// --- End IP check ---
const REFRESH_INTERVAL = 5000; // 5 seconds

function App() {
  const [events, setEvents] = useState([]);
  const [suspiciousPlayers, setSuspiciousPlayers] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState('player_id');
  const [filterText, setFilterText] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [eventsResponse, suspiciousResponse, summaryResponse] = await Promise.all([
          axios.get(EVENTS_API_URL),
          axios.get(SUSPICIOUS_API_URL),
          axios.get(SUMMARY_API_URL)
        ]);

        setEvents(eventsResponse.data);
        setSuspiciousPlayers(suspiciousResponse.data);
        setChartData(summaryResponse.data);

      } catch (error) {
        console.error("Error fetching data:", error);
        // Specifically check the error source if needed
        if (error.config && error.config.url === SUMMARY_API_URL) {
            console.error("Could not load chart data.");
             setChartData([]); // Set to empty on error for chart
        } else if (error.config && error.config.url === SUSPICIOUS_API_URL) {
            console.error("Could not load suspicious player data.");
            setSuspiciousPlayers([]); // Set to empty on error for suspicious players
        } else if (error.config && error.config.url === EVENTS_API_URL) {
             console.error("Could not load event data.");
             setEvents([]); // Set to empty on error for events
        } else {
             // General error or error from multiple sources
             setEvents([]);
             setSuspiciousPlayers([]);
             setChartData([]);
        }
      } finally {
        if (loading) setLoading(false);
      }
    };

    fetchData(); // Fetch immediately
    const intervalId = setInterval(fetchData, REFRESH_INTERVAL); // Poll every 5s
    return () => clearInterval(intervalId); // Cleanup interval
  }, [loading]); // Dependency array

  const filteredEvents = events.filter(event => {
    const filterValue = filterText.toLowerCase();
    let eventValue;
    if (filterCategory === 'details') {
      // Safely stringify details, handle if details is not an object or null
      try {
        eventValue = JSON.stringify(event.details || {}).toLowerCase();
      } catch (e) {
        eventValue = ''; // Fallback if stringify fails
      }
    } else {
      // Safely access potentially missing keys and convert to string
      eventValue = (event[filterCategory] || '').toString().toLowerCase();
    }
    return eventValue.includes(filterValue);
  });

  // Define colors for the chart lines
  const chartColors = {
      player_login: "#8884d8",
      player_logout: "#82ca9d",
      player_move: "#ffc658",
      item_pickup: "#ff7300",
      headshot: "#d0ed57"
  };

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
                  {/* Add check for suspiciousPlayers being an array */}
                  {Array.isArray(suspiciousPlayers) && suspiciousPlayers.map((player) => (
                    <tr key={player.player_id} className="suspicious-row">
                      <td>{player.player_id}</td>
                      <td>{player.reason}</td>
                      {/* Safely stringify event_counts */}
                      <td>{JSON.stringify(player.event_counts || {})}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
               {/* Add check for suspiciousPlayers being an array */}
               {(!Array.isArray(suspiciousPlayers) || suspiciousPlayers.length === 0) && <p>No suspicious players found.</p>}
            </div>

            {/* Event Summary Chart */}
            <div className="chart-container">
              <h2>Hourly Event Summary (All Time)</h2>
               {/* Add check for chartData being an array */}
              {Array.isArray(chartData) && chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart
                      data={chartData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      {/* --- XAxis Tweaks --- */}
                      <XAxis
                        dataKey="timestamp"
                        padding={{ left: 20, right: 20 }} // Add padding
                       />
                       {/* --- End XAxis --- */}
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="player_login" stroke={chartColors.player_login} name="Logins" dot={false} />
                      <Line type="monotone" dataKey="player_logout" stroke={chartColors.player_logout} name="Logouts" dot={false} />
                      <Line type="monotone" dataKey="player_move" stroke={chartColors.player_move} name="Moves" dot={false} />
                      <Line type="monotone" dataKey="item_pickup" stroke={chartColors.item_pickup} name="Pickups" dot={false} />
                      <Line type="monotone" dataKey="headshot" stroke={chartColors.headshot} name="Headshots" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
               ) : (
                  <p>No event summary data available to display chart. Run simulators to generate data.</p>
               )}
            </div>


            {/* Live Event Log Table */}
            <div className="table-container">
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
                   {/* Add check for filteredEvents being an array */}
                  {Array.isArray(filteredEvents) && filteredEvents.map((event) => (
                    <tr key={event.event_id}>
                      <td>{event.event_id}</td>
                      <td>{event.player_id}</td>
                      <td>{event.event_type}</td>
                      <td>{event.timestamp}</td>
                       {/* Safely stringify details */}
                      <td>{JSON.stringify(event.details || {})}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
               {/* Add check for filteredEvents being an array */}
              {(!Array.isArray(filteredEvents) || filteredEvents.length === 0) && <p>No events match filter.</p>}
            </div>
          </>
        )}
      </header>
    </div>
  );
}

export default App;

