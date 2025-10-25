import React, { useState, useEffect } from 'react';
import axios from 'axios';
// --- NEW: Import Recharts components ---
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
// --- END NEW ---
import './App.css'; // Corrected import path

// Define the URLs for your Flask API
const EVENTS_API_URL = 'http://127.0.0.1:5000/api/get-events';
const SUSPICIOUS_API_URL = 'http://127.0.0.1:5000/api/suspicious-players';
const SUMMARY_API_URL = 'http://127.0.0.1:5000/api/event-summary'; // <-- NEW API URL
const REFRESH_INTERVAL = 5000; // 5 seconds

function App() {
  const [events, setEvents] = useState([]);
  const [suspiciousPlayers, setSuspiciousPlayers] = useState([]);
  const [chartData, setChartData] = useState([]); // <-- NEW STATE for chart
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState('player_id');
  const [filterText, setFilterText] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      // Don't set loading on subsequent fetches to avoid flicker
      // setLoading(true); <--- Commented out or removed for polling

      try {
        // Fetch all three datasets in parallel
        const [eventsResponse, suspiciousResponse, summaryResponse] = await Promise.all([
          axios.get(EVENTS_API_URL),
          axios.get(SUSPICIOUS_API_URL),
          axios.get(SUMMARY_API_URL) // <-- NEW FETCH CALL
        ]);

        setEvents(eventsResponse.data);
        setSuspiciousPlayers(suspiciousResponse.data);

        // Check if summary data is valid before setting state
        if (summaryResponse.data && !summaryResponse.data.error) {
            setChartData(summaryResponse.data); // <-- SAVE CHART DATA
        } else {
             console.error("Error fetching summary data:", summaryResponse.data.error);
             setChartData([]); // Set to empty on error
        }


      } catch (error) {
        console.error("Error fetching data:", error);
        // Handle case where summary might fail but others succeed
        if (error.config && error.config.url === SUMMARY_API_URL) {
            console.error("Could not load chart data due to network or server error.");
             setChartData([]); // Set to empty on fetch error
        }

      } finally {
        // Set loading to false only on the initial load
        if (loading) setLoading(false);
      }
    };

    fetchData(); // Fetch immediately on component mount
    const intervalId = setInterval(fetchData, REFRESH_INTERVAL); // Set up polling interval

    // Cleanup function to clear the interval when the component unmounts
    return () => clearInterval(intervalId);
  }, [loading]); // Dependency array includes loading to set it false initially

  // Filter logic for the event log table
  const filteredEvents = events.filter(event => {
    const filterValue = filterText.toLowerCase();
    let eventValue;
    if (filterCategory === 'details') {
      eventValue = JSON.stringify(event.details).toLowerCase();
    } else {
      eventValue = (event[filterCategory] || '').toString().toLowerCase();
    }
    return eventValue.includes(filterValue);
  });

  // Define colors for the chart bars for better visual distinction
  const chartColors = {
      player_login: "#8884d8",    // Purple
      player_logout: "#82ca9d",   // Green
      player_move: "#ffc658",     // Yellow
      item_pickup: "#ff7300",     // Orange
      headshot: "#d0ed57"         // Lime Green
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
                  {suspiciousPlayers.map((player) => (
                    <tr key={player.player_id} className="suspicious-row">
                      <td>{player.player_id}</td>
                      <td>{player.reason}</td>
                      {/* Stringify the event counts object for display */}
                      <td>{JSON.stringify(player.event_counts)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
               {suspiciousPlayers.length === 0 && <p>No suspicious players found.</p>}
            </div>

            {/* --- NEW: Event Summary Chart --- */}
            <div className="chart-container">
              <h2>Hourly Event Summary</h2>
              {chartData && chartData.length > 0 ? (
                // ResponsiveContainer makes the chart adapt to screen size
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart
                    data={chartData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#555" /> {/* Grid line color */}
                    <XAxis dataKey="timestamp" stroke="#ccc"/> {/* Axis label color */}
                    <YAxis allowDecimals={false} stroke="#ccc"/> {/* Axis label color */}
                    {/* Tooltip custom style can be added via content prop if needed */}
                    <Tooltip contentStyle={{ backgroundColor: '#282c34', border: '1px solid #4CAF50' }} itemStyle={{ color: 'white' }}/>
                    <Legend wrapperStyle={{ color: '#ccc' }}/> {/* Legend text color */}
                    {/* Create a Bar component for each event type, stack them */}
                    <Bar dataKey="player_login" fill={chartColors.player_login} name="Logins" stackId="a" />
                    <Bar dataKey="player_logout" fill={chartColors.player_logout} name="Logouts" stackId="a" />
                    <Bar dataKey="player_move" fill={chartColors.player_move} name="Moves" stackId="a" />
                    <Bar dataKey="item_pickup" fill={chartColors.item_pickup} name="Pickups" stackId="a" />
                    <Bar dataKey="headshot" fill={chartColors.headshot} name="Headshots" stackId="a" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p>No summary data available to display chart. (Try generating more events)</p>
              )}
            </div>
            {/* --- END NEW CHART --- */}


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