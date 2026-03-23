import { useState, useEffect } from 'react';

const SC = s => typeof s === 'number' 
  ? s >= 80 ? 'text-emerald-400' : s >= 60 ? 'text-amber-400' : 'text-red-400'
  : 'text-slate-400';

const getMethodColor = (m) => ({
  GET: 'border-blue-500/50 text-blue-400',
  POST: 'border-violet-500/50 text-violet-400',
  PUT: 'border-amber-500/50 text-amber-400',
  DELETE: 'border-red-500/50 text-red-400'
}[m] || 'border-slate-500/50 text-slate-400');

function App() {
  const [apis, setApis] = useState([]);
  const [apisLoading, setApisLoading] = useState(true);
  const [analysisData, setAnalysisData] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setApisLoading(true);
    fetch('http://localhost:5000/api/list')
      .then(res => res.json())
      .then(data => {
        if (data.apis && Array.isArray(data.apis)) {
          setApis(data.apis.map(api => ({
            name: api.name,
            apiKey: api.apiKey,
            endpoint: api.endpoint,
            method: api.method,
            score: api.score,
            status: api.status
          })));
        }
        setApisLoading(false);
      })
      .catch(() => setApisLoading(false));
  }, []);

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
      <div className="max-w-5xl mx-auto p-8">
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-50">API Security Monitor</h1>
          </div>
          <p className="text-slate-500 text-sm">Real-time security analysis dashboard</p>
        </header>

        <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/50">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase tracking-wider">
                <th className="p-4 font-medium">Endpoint</th>
                <th className="p-4 font-medium w-24 text-center">Score</th>
                <th className="p-4 font-medium w-24 text-center">Method</th>
              </tr>
            </thead>
            <tbody>
              {apisLoading ? (
                [...Array(3)].map((_, i) => (
                  <tr key={i} className="border-b border-slate-800/50">
                    <td className="p-4"><div className="h-4 w-48 bg-slate-800 rounded animate-pulse"></div></td>
                    <td className="p-4"><div className="h-4 w-12 mx-auto bg-slate-800 rounded animate-pulse"></div></td>
                    <td className="p-4"><div className="h-4 w-16 mx-auto bg-slate-800 rounded animate-pulse"></div></td>
                  </tr>
                ))
              ) : apis.length === 0 ? (
                <tr>
                  <td colSpan="3" className="p-8 text-center text-slate-500">
                    No APIs found. Ensure the backend server is running.
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
                      <span className="text-slate-300">{api.name}</span>
                      <span className="text-slate-600 text-sm ml-2">{api.endpoint}</span>
                    </td>
                    <td className={`p-4 text-center font-bold text-lg ${SC(api.score)}`}>
                      {api.score ?? '—'}
                    </td>
                    <td className="p-4 text-center">
                      <span className={`text-xs px-2 py-1 rounded border ${getMethodColor(api.method)}`}>
                        {api.method}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

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
                      <div className="text-4xl font-bold text-slate-100">{analysisData?.security_score}</div>
                      <div className="text-slate-500 text-sm">Security Score</div>
                    </div>
                    {analysisData?.source_code && (
                      <div>
                        <h3 className="text-xs text-slate-500 uppercase mb-2">Original Source Code</h3>
                        <pre className="bg-slate-950 border border-slate-800 text-slate-300 p-4 rounded text-xs overflow-auto">
                          {analysisData.source_code}
                        </pre>
                      </div>
                    )}
                    {analysisData?.suggested_code && (
                      <div>
                        <h3 className="text-xs text-emerald-500 uppercase mb-2">Suggested Secure Code</h3>
                        <pre className="bg-emerald-950/30 border border-emerald-900/50 text-emerald-300 p-4 rounded text-xs overflow-auto">
                          {analysisData.suggested_code}
                        </pre>
                      </div>
                    )}
                    {analysisData?.suggested_dependencies && analysisData.suggested_dependencies.length > 0 && (
                      <div className="border border-amber-500/30 bg-amber-950/20 rounded-lg p-4">
                        <h3 className="text-amber-400 font-bold text-sm mb-3 flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          External Dependencies Required
                        </h3>
                        <p className="text-slate-400 text-xs mb-3">Run these commands to install required dependencies:</p>
                        <div className="bg-slate-950 rounded p-3 border border-slate-800">
                          <code className="text-emerald-400 text-sm">
                            pip install {analysisData.suggested_dependencies.join(' ')}
                          </code>
                        </div>
                        <p className="text-slate-500 text-xs mt-3">
                          Also ensure you have the necessary configuration (env variables, database connections, etc.) set up in your environment.
                        </p>
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
      </div>
    </div>
  );
}

export default App;
