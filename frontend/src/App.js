import React, { useState, useEffect } from 'react';
import axios from 'axios';
// Import Recharts components
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css'; // Ensure CSS path is correct

// Define the URLs for your Flask API
const EVENTS_API_URL = 'http://127.0.0.1:5000/api/get-events';
const SUSPICIOUS_API_URL = 'http://127.0.0.1:5000/api/suspicious-players';
const SUMMARY_API_URL = 'http://127.0.0.1:5000/api/event-summary';
const REFRESH_INTERVAL = 5000; // 5 seconds

function App() {
  const [events, setEvents] = useState([]);
  const [suspiciousPlayers, setSuspiciousPlayers] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [filterCategory, setFilterCategory] = useState('player_id');
  const [filterText, setFilterText] = useState('');

  // Fetch data function (handles loading/error states)
  const fetchData = async (isInitial = false) => {
    if (!isInitial) setIsRefreshing(true);
    setError(null);
    try {
      const [eventsResponse, suspiciousResponse, summaryResponse] = await Promise.all([
        axios.get(EVENTS_API_URL),
        axios.get(SUSPICIOUS_API_URL),
        axios.get(SUMMARY_API_URL)
      ]);
      setEvents(eventsResponse.data);
      setSuspiciousPlayers(suspiciousResponse.data);
      setChartData(summaryResponse.data);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError("Failed to load dashboard data. Check server.");
    } finally {
      if (isInitial) setIsInitialLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData(true); // Initial fetch
    const intervalId = setInterval(() => fetchData(false), REFRESH_INTERVAL); // Set up polling
    return () => clearInterval(intervalId); // Cleanup
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only on mount

  // Filter logic for event log
  const filteredEvents = events.filter(event => {
    const filterValue = filterText.toLowerCase();
    let eventValue;
    if (filterCategory === 'details') {
      try { eventValue = JSON.stringify(event.details || {}).toLowerCase(); }
      catch (e) { eventValue = ''; }
    } else {
      eventValue = (event[filterCategory] || '').toString().toLowerCase();
    }
    return eventValue.includes(filterValue);
  });

  // Chart colors (includes CoD event types)
  const chartColors = {
      player_login: "#8884d8", player_logout: "#82ca9d", player_move: "#ffc658",
      kill: "#FF0000", death: "#A9A9A9", objective_capture: "#00BFFF",
      reload: "#FFA500", grenade_throw: "#FF69B4", weapon_pickup: "#BA55D3",
      headshot: "#d0ed57"
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Game Security Dashboard</h1>
        {isRefreshing && <p className="refreshing-indicator">Updating...</p>}
        {error && <p className="error-message">{error}</p>}

        {isInitialLoading ? (
          <p>Loading dashboard...</p>
        ) : (
          !error && (
            <>
              {/* Suspicious Players Table */}
              <div className="table-container">
                <h2>Suspicious Players (Flagged by ML Model)</h2>
                <table>
                   <thead>
                    <tr>
                      <th>Player ID</th>
                      <th>Reason</th>
                      <th>KDR</th>
                      <th>HS % (of Total Kills)</th>
                      <th>Total Kills</th>
                      <th>Deaths</th>
                      <th>Headshots</th>
                    </tr>
                   </thead>
                   <tbody>
                    {Array.isArray(suspiciousPlayers) && suspiciousPlayers.map((player) => (
                      <tr key={player.player_id} className="suspicious-row">
                        <td>{player.player_id}</td>
                        <td>{player.reason}</td>
                        <td>{player.stats?.kdr ?? 'N/A'}</td>
                        <td>{player.stats?.hs_ratio ?? 'N/A'}%</td>
                        <td>{player.stats?.total_kills ?? 'N/A'}</td>
                        <td>{player.stats?.deaths ?? 'N/A'}</td>
                        <td>{player.stats?.headshots ?? 'N/A'}</td>
                      </tr>
                    ))}
                   </tbody>
                </table>
                 {(!Array.isArray(suspiciousPlayers) || suspiciousPlayers.length === 0) && <p>No suspicious players found.</p>}
              </div>

              {/* Event Summary Chart */}
              <div className="chart-container">
                <h2>5-Minute Event Summary (All Time)</h2>
                {Array.isArray(chartData) && chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="timestamp" padding={{ left: 20, right: 20 }}/>
                        <YAxis allowDecimals={false} />
                        <Tooltip />
                        {/* --- ADDED wrapperStyle for spacing --- */}
                        <Legend
                          layout="vertical"
                          verticalAlign="middle"
                          align="right"
                          wrapperStyle={{ paddingLeft: "20px" }} // Add left padding to push it away from chart
                        />
                        {/* --- END ADDED --- */}
                        <Line type="monotone" dataKey="player_login" stroke={chartColors.player_login} name="Logins" dot={false} />
                        <Line type="monotone" dataKey="player_logout" stroke={chartColors.player_logout} name="Logouts" dot={false} />
                        <Line type="monotone" dataKey="player_move" stroke={chartColors.player_move} name="Moves" dot={false} />
                        <Line type="monotone" dataKey="kill" stroke={chartColors.kill} name="Kills" dot={false} />
                        <Line type="monotone" dataKey="death" stroke={chartColors.death} name="Deaths" dot={false} />
                        <Line type="monotone" dataKey="objective_capture" stroke={chartColors.objective_capture} name="Objectives" dot={false} />
                        <Line type="monotone" dataKey="reload" stroke={chartColors.reload} name="Reloads" dot={false} />
                        <Line type="monotone" dataKey="grenade_throw" stroke={chartColors.grenade_throw} name="Grenades" dot={false} />
                        <Line type="monotone" dataKey="weapon_pickup" stroke={chartColors.weapon_pickup} name="Wpn Pickups" dot={false} />
                        <Line type="monotone" dataKey="headshot" stroke={chartColors.headshot} name="Headshots" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                 ) : (
                    error ? <p>Could not load chart data.</p> : <p>No event summary data available.</p>
                 )}
              </div>


              {/* Live Event Log Table */}
              <div className="table-container">
                <div className="filter-container">
                   <h2>Live Event Log (Auto-Refreshes every 5s)</h2>
                   <div className="filter-controls">
                     <label htmlFor="filter-category" className="filter-label">Filter by:</label>
                     <select id="filter-category" className="filter-select" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                       <option value="player_id">Player ID</option>
                       <option value="event_type">Event Type</option>
                       <option value="timestamp">Timestamp</option>
                       <option value="event_id">Event ID</option>
                       <option value="details">Details</option>
                     </select>
                     <input type="text" placeholder="Search value..." className="filter-input" value={filterText} onChange={(e) => setFilterText(e.target.value)} />
                   </div>
                </div>
                 <table>
                   <thead>
                    <tr><th>Event ID</th><th>Player ID</th><th>Event Type</th><th>Timestamp</th><th>Details</th></tr>
                   </thead>
                   <tbody>
                    {Array.isArray(filteredEvents) && filteredEvents.map((event) => (
                      <tr key={event.event_id}>
                        <td>{event.event_id}</td>
                        <td>{event.player_id}</td>
                        <td>{event.event_type}</td>
                        <td>{event.timestamp}</td>
                        <td>{JSON.stringify(event.details || {})}</td>
                      </tr>
                    ))}
                   </tbody>
                </table>
                {(!Array.isArray(filteredEvents) || filteredEvents.length === 0) && <p>No events match filter.</p>}
              </div>
            </>
          )
        )}
      </header>
    </div>
  );
}

export default App;