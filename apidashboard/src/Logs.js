import { useState, useEffect } from 'react';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [limit, setLimit] = useState(50);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Fetch logs on component mount and when filters change
  useEffect(() => {
    fetchLogs();
    fetchStats();
  }, [limit, statusFilter, filter]);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchLogs();
      fetchStats();
    }, 3000); // Refresh every 3 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, limit, statusFilter, filter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('limit', limit);
      if (statusFilter) params.append('status', statusFilter);
      if (filter) params.append('api_path', filter);

      const response = await fetch(`http://localhost:5000/api/logs?${params}`);
      const data = await response.json();
      setLogs(data.logs || []);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/logs/stats');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const getStatusBadge = (status) => {
    if (status === 'accepted') {
      return (
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-emerald-900/30 text-emerald-400 border border-emerald-500/50">
          ✅ Accepted
        </span>
      );
    } else if (status === 'rejected') {
      return (
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-red-900/30 text-red-400 border border-red-500/50">
          ❌ Rejected
        </span>
      );
    }
    return (
      <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-slate-900/30 text-slate-400 border border-slate-500/50">
        ? Unknown
      </span>
    );
  };

  const getMethodColor = (method) => {
    const colors = {
      GET: 'text-blue-400',
      POST: 'text-violet-400',
      PUT: 'text-amber-400',
      DELETE: 'text-red-400',
      PATCH: 'text-cyan-400'
    };
    return colors[method] || 'text-slate-400';
  };

  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const formatTimeAgo = (timestamp) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const seconds = Math.floor((now - date) / 1000);
      
      if (seconds < 60) return `${seconds}s ago`;
      if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
      if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
      return `${Math.floor(seconds / 86400)}d ago`;
    } catch {
      return 'N/A';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
            API Request Logs
          </h1>
          <p className="text-slate-400">Monitor API hits and middleware security status</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-6 backdrop-blur-sm">
              <div className="text-slate-400 text-sm mb-1">Total Requests</div>
              <div className="text-3xl font-bold text-slate-100">{stats.total_requests}</div>
            </div>
            <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-6 backdrop-blur-sm">
              <div className="text-emerald-400 text-sm mb-1">✅ Accepted</div>
              <div className="text-3xl font-bold text-emerald-400">{stats.accepted}</div>
              {stats.total_requests > 0 && (
                <div className="text-xs text-slate-400 mt-1">
                  {((stats.accepted / stats.total_requests) * 100).toFixed(1)}%
                </div>
              )}
            </div>
            <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-6 backdrop-blur-sm">
              <div className="text-red-400 text-sm mb-1">❌ Rejected</div>
              <div className="text-3xl font-bold text-red-400">{stats.rejected}</div>
              {stats.total_requests > 0 && (
                <div className="text-xs text-slate-400 mt-1">
                  {((stats.rejected / stats.total_requests) * 100).toFixed(1)}%
                </div>
              )}
            </div>
            <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-6 backdrop-blur-sm">
              <div className="text-slate-400 text-sm mb-1">Unique APIs</div>
              <div className="text-3xl font-bold text-slate-100">
                {Object.keys(stats.apis || {}).length}
              </div>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-6 mb-8 backdrop-blur-sm">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            {/* API Path Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Filter by API Path
              </label>
              <input
                type="text"
                placeholder="e.g., login, user, payment"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Filter by Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:border-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="accepted">✅ Accepted</option>
                <option value="rejected">❌ Rejected</option>
              </select>
            </div>

            {/* Limit */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Show Logs
              </label>
              <select
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:outline-none focus:border-blue-500"
              >
                <option value="25">Last 25</option>
                <option value="50">Last 50</option>
                <option value="100">Last 100</option>
                <option value="200">Last 200</option>
              </select>
            </div>

            {/* Auto Refresh Toggle */}
            <div className="flex items-end">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`w-full px-4 py-2 rounded-lg font-medium transition-all ${
                  autoRefresh
                    ? 'bg-blue-600 text-white border border-blue-500'
                    : 'bg-slate-800 text-slate-300 border border-slate-600 hover:border-slate-500'
                }`}
              >
                {autoRefresh ? '⏸️ Auto-Refresh ON' : '▶️ Start Auto-Refresh'}
              </button>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => fetchLogs()}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-all"
            >
              {loading ? '⟳ Refreshing...' : '🔄 Refresh'}
            </button>
            <button
              onClick={() => {
                setFilter('');
                setStatusFilter('');
                setLimit(50);
                setAutoRefresh(false);
              }}
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 font-medium transition-all border border-slate-600"
            >
              🔄 Reset Filters
            </button>
          </div>
        </div>

        {/* Logs Table */}
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg overflow-hidden backdrop-blur-sm">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-800/50">
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    API Path
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Method
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody>
                {logs.length > 0 ? (
                  logs.map((log, index) => (
                    <tr
                      key={index}
                      className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="px-6 py-4 text-sm text-slate-300 whitespace-nowrap">
                        <div title={formatTime(log.timestamp)}>
                          {formatTimeAgo(log.timestamp)}
                        </div>
                        <div className="text-xs text-slate-500">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <code className="bg-slate-800/50 px-3 py-1 rounded text-blue-400 font-mono">
                          /{log.api_path}
                        </code>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`font-semibold ${getMethodColor(log.method)}`}>
                          {log.method}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {getStatusBadge(log.status)}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {log.reason}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                      {loading ? (
                        <div className="flex justify-center items-center gap-2">
                          <div className="animate-spin">⟳</div>
                          Loading logs...
                        </div>
                      ) : (
                        'No logs found. Make some API requests to see them here!'
                      )}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer Info */}
        {logs.length > 0 && (
          <div className="mt-4 text-sm text-slate-500">
            Showing {logs.length} of {stats?.total_requests || 0} total requests
          </div>
        )}
      </div>
    </div>
  );
};

export default Logs;
