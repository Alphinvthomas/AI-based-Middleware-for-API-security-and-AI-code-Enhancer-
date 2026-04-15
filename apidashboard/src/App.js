import { useState, useEffect } from 'react';
import Logs from './Logs';

const SC = s => typeof s === 'number' 
  ? s >= 80 ? 'text-emerald-400' : s >= 60 ? 'text-amber-400' : 'text-red-400'
  : 'text-slate-400';

const getMethodColor = (m) => ({
  GET: 'border-blue-500/50 text-blue-400',
  POST: 'border-violet-500/50 text-violet-400',
  PUT: 'border-amber-500/50 text-amber-400',
  DELETE: 'border-red-500/50 text-red-400',
  PATCH: 'border-cyan-500/50 text-cyan-400'
}[m] || 'border-slate-500/50 text-slate-400');

// Parse GitHub URL to extract owner and repo
const parseGitHubUrl = (url) => {
  try {
    const match = url.match(/github\.com[:/]([^/]+)\/([^/]+?)(\.git)?$/i);
    if (match) {
      return { owner: match[1], repo: match[2] };
    }
    return null;
  } catch {
    return null;
  }
};

function App() {
  const [repoUrl, setRepoUrl] = useState('https://github.com/AswinRaj1123/RentMate');
  const [apis, setApis] = useState([]);
  const [apisLoading, setApisLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [discoveryStatus, setDiscoveryStatus] = useState('');
  const [stats, setStats] = useState({ total: 0, active: 0, danger: 0, languages: {} });
  const [currentPage, setCurrentPage] = useState('dashboard'); // 'dashboard' or 'logs'

  // Parse and auto-discover on load and when repo changes
  useEffect(() => {
    const initializeRepo = async () => {
      const parsed = parseGitHubUrl(repoUrl);
      if (parsed) {
        await discoverAPIs(parsed.owner, parsed.repo);
      }
    };
    initializeRepo();
  }, []);

  const discoverAPIs = async (owner, repo) => {
    setApisLoading(true);
    setDiscoveryStatus('🔍 Discovering APIs...');
    setApis([]);
    setStats({ total: 0, active: 0, danger: 0, languages: {} });

    try {
      const body = JSON.stringify({ owner, repo_name: repo });
      const response = await fetch('http://localhost:5000/api/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body
      });

      if (!response.ok) {
        setDiscoveryStatus('❌ Failed to discover APIs');
        setApisLoading(false);
        return;
      }

      const data = await response.json();
      setDiscoveryStatus(`✅ Discovered ${data.total_apis} APIs`);

      // Transform and set APIs
      const transformedApis = data.apis.map(api => ({
        name: api.name,
        apiKey: api.name,
        endpoint: api.endpoint,
        method: api.http_method,
        score: api.security_score,
        status: api.status,
        language: api.language,
        framework: api.framework,
        file_path: api.file_path
      }));

      setApis(transformedApis);

      // Calculate stats
      const active = transformedApis.filter(a => a.status === 'Active').length;
      const danger = transformedApis.filter(a => a.status === 'Danger').length;
      const languages = {};
      transformedApis.forEach(api => {
        languages[api.language] = (languages[api.language] || 0) + 1;
      });

      setStats({
        total: transformedApis.length,
        active,
        danger,
        languages
      });

      setTimeout(() => setDiscoveryStatus(''), 3000);
    } catch (error) {
      setDiscoveryStatus(`❌ Error: ${error.message}`);
    } finally {
      setApisLoading(false);
    }
  };

  const handleAnalyzeRepo = async () => {
    const parsed = parseGitHubUrl(repoUrl);
    if (!parsed) {
      setDiscoveryStatus('❌ Invalid GitHub URL format');
      return;
    }
    await discoverAPIs(parsed.owner, parsed.repo);
  };

  const fetchAPIAnalysis = async (apiKey) => {
    setLoading(true);
    setShowModal(true);
    try {
      const res = await fetch(`http://localhost:5000/api/analyze/${apiKey}`);
      setAnalysisData(await res.json());
    } catch {
      setAnalysisData({ error: 'Failed to load analysis' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-mono">
      <div className="max-w-6xl mx-auto p-8">
        {/* Navigation Tabs */}
        <div className="mb-8 flex gap-4 border-b border-slate-800">
          <button
            onClick={() => setCurrentPage('dashboard')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              currentPage === 'dashboard'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            📊 Dashboard
          </button>
          <button
            onClick={() => setCurrentPage('logs')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              currentPage === 'logs'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            📋 Request Logs
          </button>
        </div>

        {/* Dashboard Page */}
        {currentPage === 'dashboard' ? (
          <>
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-50">API Security Analyzer</h1>
          </div>
          <p className="text-slate-500 text-sm">Analyze GitHub repositories for API security vulnerabilities</p>
        </header>

        {/* Repository Input Section */}
        <div className="mb-8 border border-slate-800 rounded-lg bg-slate-900/50 p-6">
          <h2 className="text-lg font-bold mb-4 text-slate-100">📂 GitHub Repository</h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/username/repo-name"
              className="flex-1 bg-slate-800 border border-slate-700 rounded px-4 py-2 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
            <button
              onClick={handleAnalyzeRepo}
              disabled={apisLoading}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded text-sm font-medium transition-colors"
            >
              {apisLoading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
          {discoveryStatus && (
            <p className="text-slate-400 text-sm mt-3">{discoveryStatus}</p>
          )}
        </div>

        {/* Statistics Cards */}
        {stats.total > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="border border-slate-800 rounded-lg bg-slate-900/50 p-4">
              <div className="text-2xl font-bold text-slate-100">{stats.total}</div>
              <div className="text-slate-500 text-xs uppercase mt-1">Total APIs</div>
            </div>
            <div className="border border-emerald-800/50 rounded-lg bg-emerald-950/20 p-4">
              <div className="text-2xl font-bold text-emerald-400">{stats.active}</div>
              <div className="text-emerald-600 text-xs uppercase mt-1">✓ Active</div>
            </div>
            <div className="border border-red-800/50 rounded-lg bg-red-950/20 p-4">
              <div className="text-2xl font-bold text-red-400">{stats.danger}</div>
              <div className="text-red-600 text-xs uppercase mt-1">⚠ Danger</div>
            </div>
            <div className="border border-slate-800 rounded-lg bg-slate-900/50 p-4">
              <div className="text-sm font-bold text-slate-100">
                {Object.entries(stats.languages).map(([lang, count]) => (
                  <div key={lang}>{lang}</div>
                ))}
              </div>
              <div className="text-slate-500 text-xs uppercase mt-1">Languages</div>
            </div>
          </div>
        )}

        {/* APIs Table */}
        <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/50">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase tracking-wider bg-slate-900/80">
                <th className="p-4 font-medium">Endpoint</th>
                <th className="p-4 font-medium w-20 text-center">Score</th>
                <th className="p-4 font-medium w-28 text-center">Method</th>
                <th className="p-4 font-medium w-28 text-center">Language</th>
                <th className="p-4 font-medium w-24 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {apisLoading && apis.length === 0 ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="border-b border-slate-800/50">
                    <td className="p-4"><div className="h-4 w-48 bg-slate-800 rounded animate-pulse"></div></td>
                    <td className="p-4"><div className="h-4 w-12 mx-auto bg-slate-800 rounded animate-pulse"></div></td>
                    <td className="p-4"><div className="h-4 w-16 mx-auto bg-slate-800 rounded animate-pulse"></div></td>
                    <td className="p-4"><div className="h-4 w-16 mx-auto bg-slate-800 rounded animate-pulse"></div></td>
                    <td className="p-4"><div className="h-4 w-16 mx-auto bg-slate-800 rounded animate-pulse"></div></td>
                  </tr>
                ))
              ) : apis.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-slate-500">
                    Enter a GitHub repository URL to start analysis
                  </td>
                </tr>
              ) : (
                apis.map((api, i) => (
                  <tr
                    key={i}
                    onClick={() => fetchAPIAnalysis(api.apiKey)}
                    className="border-b border-slate-800/50 hover:bg-slate-800/30 cursor-pointer transition-colors"
                  >
                    <td className="p-4">
                      <div className="text-slate-300 text-sm">{api.name}</div>
                      <div className="text-slate-600 text-xs mt-1">{api.endpoint}</div>
                      <div className="text-slate-700 text-xs mt-1">{api.file_path}</div>
                    </td>
                    <td className={`p-4 text-center font-bold text-lg ${SC(api.score)}`}>
                      {api.score ?? '—'}
                    </td>
                    <td className="p-4 text-center">
                      <span className={`text-xs px-2 py-1 rounded border ${getMethodColor(api.method)}`}>
                        {api.method}
                      </span>
                    </td>
                    <td className="p-4 text-center text-slate-400 text-sm">
                      {api.language}
                    </td>
                    <td className="p-4 text-center">
                      <span className={`text-xs px-2 py-1 rounded ${api.status === 'Active' ? 'bg-emerald-950/50 text-emerald-400' : 'bg-red-950/50 text-red-400'}`}>
                        {api.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Analysis Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4" onClick={() => setShowModal(false)}>
            <div className="bg-slate-900 border border-slate-700 rounded-lg w-full max-w-3xl max-h-[85vh] overflow-hidden" onClick={e => e.stopPropagation()}>
              <div className="p-6 border-b border-slate-800">
                <h2 className="text-lg font-bold text-slate-100">Security Analysis</h2>
              </div>
              <div className="p-6 overflow-auto max-h-[calc(85vh-80px)]">
                {loading ? (
                  <p className="text-slate-500">Analyzing...</p>
                ) : analysisData?.error ? (
                  <p className="text-red-400">{analysisData.error}</p>
                ) : (
                  <div className="space-y-6">
                    <div className="flex items-center gap-4">
                      <div className={`text-4xl font-bold ${SC(analysisData?.security_score)}`}>{analysisData?.security_score}</div>
                      <div className="text-slate-500 text-sm">Security Score</div>
                    </div>
                    {analysisData?.source_code && (
                      <div>
                        <h3 className="text-xs text-slate-500 uppercase mb-2">Original Source Code</h3>
                        <pre className="bg-slate-950 border border-slate-800 text-slate-300 p-4 rounded text-xs overflow-auto max-h-64">
                          {analysisData.source_code}
                        </pre>
                      </div>
                    )}
                    {analysisData?.suggested_code && (
                      <div>
                        <h3 className="text-xs text-emerald-500 uppercase mb-2">Suggested Secure Code</h3>
                        <pre className="bg-emerald-950/30 border border-emerald-900/50 text-emerald-300 p-4 rounded text-xs overflow-auto max-h-64">
                          {analysisData.suggested_code}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="p-4 border-t border-slate-800 flex justify-end gap-3">
                <button onClick={() => setShowModal(false)} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm text-slate-300 transition-colors">
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
          </>
        ) : (
          <Logs />
        )}
      </div>
    </div>
  );
}

export default App;
