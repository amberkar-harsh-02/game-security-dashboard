import React, { useState, useEffect } from 'react';
import axios from 'axios';
// Import Recharts components
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

// Define the URLs for your Flask API
const EVENTS_API_URL = 'http://127.0.0.1:5000/api/get-events';
const SUSPICIOUS_API_URL = 'http://127.0.0.1:5000/api/suspicious-players';
const SUMMARY_API_URL = 'http://127.0.0.1:5000/api/event-summary';
const REFRESH_INTERVAL = 5000; // 5 seconds

function App() {
  // Existing states
  const [events, setEvents] = useState([]);
  const [suspiciousPlayers, setSuspiciousPlayers] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [filterCategory, setFilterCategory] = useState('player_id');
  const [filterText, setFilterText] = useState('');

  // --- NEW: State for Player Drill-Down Modal ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPlayerData, setSelectedPlayerData] = useState(null); // Will hold { playerInfo: {...}, recentEvents: [...] }
  // --- END NEW ---

  // Fetch data function (remains the same)
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
    fetchData(true);
    const intervalId = setInterval(() => fetchData(false), REFRESH_INTERVAL);
    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Filter logic for event log (remains the same)
  const filteredEvents = events.filter(event => {
    // ... filter logic ...
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

  // Chart colors (remains the same)
  const chartColors = { /* ... */
      player_login: "#8884d8", player_logout: "#82ca9d", player_move: "#ffc658",
      kill: "#FF0000", death: "#A9A9A9", objective_capture: "#00BFFF",
      reload: "#FFA500", grenade_throw: "#FF69B4", weapon_pickup: "#BA55D3",
      headshot: "#d0ed57"
  };

  // --- NEW: Functions to handle modal ---
  const handlePlayerClick = (playerId) => {
    // Find player stats (if they are in the suspicious list)
    const playerInfo = suspiciousPlayers.find(p => p.player_id === playerId);

    // Find recent events for this player from the main log (e.g., last 10)
    const recentEvents = events.filter(e => e.player_id === playerId).slice(0, 10);

    setSelectedPlayerData({
      playerInfo: playerInfo, // This might be undefined if player isn't suspicious
      recentEvents: recentEvents,
      playerId: playerId // Always include the ID
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedPlayerData(null); // Clear data when closing
  };
  // --- END NEW FUNCTIONS ---

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
                      <th>KDR</th><th>HS %</th><th>Move %</th>
                      <th>Total Kills</th><th>Deaths</th><th>Headshots</th>
                      <th>Moves</th><th>Total Events</th>
                    </tr>
                   </thead>
                   <tbody>
                    {Array.isArray(suspiciousPlayers) && suspiciousPlayers.map((player) => (
                      <tr key={player.player_id} className="suspicious-row">
                        {/* --- MODIFIED: Make Player ID clickable --- */}
                        <td>
                          <span className="clickable-player-id" onClick={() => handlePlayerClick(player.player_id)}>
                            {player.player_id}
                          </span>
                        </td>
                        {/* --- END MODIFIED --- */}
                        <td>{player.reason}</td>
                        <td>{player.stats?.kdr ?? 'N/A'}</td>
                        <td>{player.stats?.hs_ratio ?? 'N/A'}%</td>
                        <td>{player.stats?.move_ratio ?? 'N/A'}%</td>
                        <td>{player.stats?.total_kills ?? 'N/A'}</td>
                        <td>{player.stats?.deaths ?? 'N/A'}</td>
                        <td>{player.stats?.headshots ?? 'N/A'}</td>
                        <td>{player.stats?.moves ?? 'N/A'}</td>
                        <td>{player.stats?.total_events ?? 'N/A'}</td>
                      </tr>
                    ))}
                   </tbody>
                </table>
                 {(!Array.isArray(suspiciousPlayers) || suspiciousPlayers.length === 0) && <p>No suspicious players found.</p>}
              </div>

              {/* Event Summary Chart (remains the same) */}
              <div className="chart-container">
                 {/* ... chart code ... */}
                 <h2>5-Minute Event Summary (All Time)</h2>
                {Array.isArray(chartData) && chartData.length > 0 ? ( <ResponsiveContainer width="100%" height={300}> <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}> <CartesianGrid strokeDasharray="3 3" /> <XAxis dataKey="timestamp" padding={{ left: 20, right: 20 }}/> <YAxis allowDecimals={false} /> <Tooltip /> <Legend layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{ paddingLeft: "20px" }}/> <Line type="monotone" dataKey="player_login" stroke={chartColors.player_login} name="Logins" dot={false} /> <Line type="monotone" dataKey="player_logout" stroke={chartColors.player_logout} name="Logouts" dot={false} /> <Line type="monotone" dataKey="player_move" stroke={chartColors.player_move} name="Moves" dot={false} /> <Line type="monotone" dataKey="kill" stroke={chartColors.kill} name="Kills" dot={false} /> <Line type="monotone" dataKey="death" stroke={chartColors.death} name="Deaths" dot={false} /> <Line type="monotone" dataKey="objective_capture" stroke={chartColors.objective_capture} name="Objectives" dot={false} /> <Line type="monotone" dataKey="reload" stroke={chartColors.reload} name="Reloads" dot={false} /> <Line type="monotone" dataKey="grenade_throw" stroke={chartColors.grenade_throw} name="Grenades" dot={false} /> <Line type="monotone" dataKey="weapon_pickup" stroke={chartColors.weapon_pickup} name="Wpn Pickups" dot={false} /> <Line type="monotone" dataKey="headshot" stroke={chartColors.headshot} name="Headshots" dot={false} /> </LineChart> </ResponsiveContainer> ) : ( error ? <p>Could not load chart data.</p> : <p>No event summary data available.</p> )}
              </div>


              {/* Live Event Log Table */}
              <div className="table-container">
                <div className="filter-container">
                   <h2>Live Event Log (Auto-Refreshes every 5s)</h2>
                   <div className="filter-controls">
                     {/* ... filter controls ... */}
                      <label htmlFor="filter-category" className="filter-label">Filter by:</label>
                     <select id="filter-category" className="filter-select" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                       <option value="player_id">Player ID</option> <option value="event_type">Event Type</option> <option value="timestamp">Timestamp</option> <option value="event_id">Event ID</option> <option value="details">Details</option>
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
                        {/* --- MODIFIED: Make Player ID clickable --- */}
                        <td>
                          <span className="clickable-player-id" onClick={() => handlePlayerClick(event.player_id)}>
                            {event.player_id}
                          </span>
                        </td>
                        {/* --- END MODIFIED --- */}
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

      {/* --- NEW: Player Detail Modal --- */}
      {isModalOpen && selectedPlayerData && (
        <div className="modal-overlay" onClick={closeModal}> {/* Close on overlay click */}
          <div className="modal-content" onClick={(e) => e.stopPropagation()}> {/* Prevent closing when clicking inside modal */}
            <h2>Player Details: {selectedPlayerData.playerId}</h2>
            <button className="modal-close-button" onClick={closeModal}>X</button>

            {/* Display Player Stats if available (i.e., if player was suspicious) */}
            {selectedPlayerData.playerInfo ? (
              <div className="modal-stats">
                <h3>Suspicion Details:</h3>
                <p><strong>Reason:</strong> {selectedPlayerData.playerInfo.reason}</p>
                <p><strong>KDR:</strong> {selectedPlayerData.playerInfo.stats?.kdr ?? 'N/A'}</p>
                <p><strong>HS %:</strong> {selectedPlayerData.playerInfo.stats?.hs_ratio ?? 'N/A'}%</p>
                <p><strong>Move %:</strong> {selectedPlayerData.playerInfo.stats?.move_ratio ?? 'N/A'}%</p>
                <p><strong>Total Kills:</strong> {selectedPlayerData.playerInfo.stats?.total_kills ?? 'N/A'}</p>
                <p><strong>Deaths:</strong> {selectedPlayerData.playerInfo.stats?.deaths ?? 'N/A'}</p>
                <p><strong>Headshots:</strong> {selectedPlayerData.playerInfo.stats?.headshots ?? 'N/A'}</p>
                <p><strong>Moves:</strong> {selectedPlayerData.playerInfo.stats?.moves ?? 'N/A'}</p>
                <p><strong>Total Events:</strong> {selectedPlayerData.playerInfo.stats?.total_events ?? 'N/A'}</p>
              </div>
            ) : (
              <p><i>This player was not flagged as suspicious in the current data.</i></p>
            )}

            {/* Display Recent Events */}
            <div className="modal-events">
              <h3>Recent Events (Max 10):</h3>
              {selectedPlayerData.recentEvents.length > 0 ? (
                <table className="modal-event-table">
                  <thead>
                    <tr><th>Timestamp</th><th>Event Type</th><th>Details</th></tr>
                  </thead>
                  <tbody>
                    {selectedPlayerData.recentEvents.map(event => (
                      <tr key={event.event_id}>
                        <td>{event.timestamp}</td>
                        <td>{event.event_type}</td>
                        <td>{JSON.stringify(event.details || {})}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p>No recent events found in the current log for this player.</p>
              )}
            </div>
          </div>
        </div>
      )}
      {/* --- END NEW MODAL --- */}

    </div>
  );
}

export default App;