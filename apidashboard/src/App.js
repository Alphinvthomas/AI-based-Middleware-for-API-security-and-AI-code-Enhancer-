import { useState } from 'react';
import { login } from './apis/login';

const DEFAULT_APIS = [
  { name:"Auth Service",      ep:"/api/v2/auth",         hit:"2 min ago",   score:97, method:"POST",  status:"Active",   apiKey:"login"   },
  { name:"User Profile",      ep:"/api/v2/users/:id",    hit:"8 min ago",   score:91, method:"GET",   status:"Active",   apiKey:"get_users"   },
  { name:"Payment Gateway",   ep:"/api/v1/payments",     hit:"1 min ago",   score:88, method:"POST",  status:"Active",   apiKey:"process_payment"   },
  { name:"Notification Push", ep:"/api/v3/notify",       hit:"15 min ago",  score:74, method:"POST",  status:"Danger",   apiKey:"notify"   },
  { name:"Product Catalog",   ep:"/api/v2/products",     hit:"3 min ago",   score:95, method:"GET",   status:"Active",   apiKey:"products"   },
  { name:"Search Engine",     ep:"/api/v1/search",       hit:"6 min ago",   score:83, method:"GET",   status:"Active",   apiKey:"search"   },
  { name:"Analytics Ingest",  ep:"/api/v2/analytics",    hit:"32 min ago",  score:60, method:"PUT",   status:"Danger",   apiKey:"analytics"   },
  { name:"Email Service",     ep:"/api/v1/email/send",   hit:"2 hrs ago",   score:45, method:"POST",  status:"Inactive", apiKey:"email"   },
  { name:"File Upload CDN",   ep:"/api/v2/upload",       hit:"11 min ago",  score:90, method:"POST",  status:"Active",   apiKey:"upload"   },
  { name:"Order Management",  ep:"/api/v3/orders",       hit:"4 min ago",   score:93, method:"GET",   status:"Active",   apiKey:"orders"   },
  { name:"Inventory Sync",    ep:"/api/v1/inventory",    hit:"47 min ago",  score:38, method:"PATCH", status:"Inactive", apiKey:"inventory"   },
  { name:"Geo Location",      ep:"/api/v2/geo",          hit:"19 min ago",  score:78, method:"GET",   status:"Active",   apiKey:"geo"   },
];

const MC = { GET:"bg-blue-50 text-blue-600", POST:"bg-violet-50 text-violet-600",
             PUT:"bg-amber-50 text-amber-600", PATCH:"bg-teal-50 text-teal-600", DELETE:"bg-red-50 text-red-600" };

const SC = s => s>=80?"score-h":s>=60?"score-m":"score-l";

const getBadge = (s) => {
  const m={Active:{c:"badge-active",d:"dot-active"},Inactive:{c:"badge-inactive",d:"dot-inactive"},Degraded:{c:"badge-degraded",d:"dot-degraded"},Danger:{c:"badge-danger",d:"dot-danger"}};
  const x=m[s]||m.Inactive;
  return { className: `badge ${x.c}`, dotClassName: `badge-dot ${x.d}`, text: s };
};

const getSeverityBadge = (severity) => {
  const colors = {
    Critical: "bg-red-100 text-red-800 border-red-300",
    High: "bg-orange-100 text-orange-800 border-orange-300",
    Medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
    Low: "bg-green-100 text-green-800 border-green-300"
  };
  return colors[severity] || colors.Medium;
};

function App() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedAPI, setSelectedAPI] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [apis, setApis] = useState(DEFAULT_APIS);

  const [loggedIn, setLoggedIn] = useState(false);
  const [loginEmail, setLoginEmail] = useState("testemail@email.com");
  const [loginPassword, setLoginPassword] = useState("test12345");
  const [loginError, setLoginError] = useState(null);

  const doLogin = async (e) => {
    e.preventDefault();
    setLoginError(null);

    const result = await login({ email: loginEmail, password: loginPassword });
    if (result?.status === "ok") {
      setLoggedIn(true);
      return;
    }

    setLoginError(result?.message || "Login failed");
  };


  const fetchAPIAnalysis = async (apiKey, apiName) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:5000/api/analyze/${apiKey}`);
      if (!response.ok) {
        throw new Error(`Failed to analyze API: ${response.statusText}`);
      }
      const data = await response.json();
      setAnalysisData(data);
      setSelectedAPI(apiName);
      setShowModal(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedAPI(null);
    setAnalysisData(null);
    setError(null);
  };

  const filteredAPIs = apis.filter(a =>
    (statusFilter === 'all' || a.status === statusFilter) &&
    (a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.ep.toLowerCase().includes(search.toLowerCase()))
  );

  // const stats = [
  //   { label: "Total APIs", val: APIS.length, icon: "🔌", sub: "endpoints registered", tc: "text-indigo-600", bg: "bg-indigo-50" },
  //   { label: "Active", val: APIS.filter(a=>a.status==="Active").length, icon: "✅", sub: "operational now", tc: "text-emerald-600", bg: "bg-emerald-50" },
  //   { label: "Avg Security", val: Math.round(APIS.reduce((s,a)=>s+a.score,0)/APIS.length), icon: "🔒", sub: "security score avg", tc: "text-violet-600", bg: "bg-violet-50" },
  //   { label: "Degraded", val: APIS.filter(a=>a.status==="Degraded").length, icon: "⚠️", sub: "needs attention", tc: "text-amber-600", bg: "bg-amber-50" },
  // ];

  return (
    <div>
      {!loggedIn ? (
        <div className="min-h-screen flex items-center justify-center bg-slate-100 p-6">
          <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Login to API Defender</h2>
            <p className="text-sm text-gray-500 mb-6">Use the test credentials below to continue.</p>

            <form onSubmit={doLogin} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-600">Email</label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full mt-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-200"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600">Password</label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full mt-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-200"
                />
              </div>

              {loginError && (
                <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-4 py-3">
                  {loginError}
                </div>
              )}

              <button
                type="submit"
                className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition"
              >
                Sign In
              </button>

              <div className="text-xs text-gray-500">
                Use: <strong>testemail@email.com</strong> / <strong>test12345</strong>
              </div>
            </form>
          </div>
        </div>
      ) : (
        <>
          <div className="header-gradient rounded-2xl p-6 md:p-8 mb-8 text-blue-300 shadow-xl relative overflow-hidden">
            <div className="absolute inset-0 opacity-10" style={{backgroundImage:"radial-gradient(circle at 80% 20%,blue 1px,transparent 1px)", backgroundSize:"28px 28px"}}></div>
            <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <div className="w-9 h-9 bg-green-500/20 rounded-xl flex items-center justify-center text-lg">⚡</div>
                  <span className="text-blue-400 text-md font-bold tracking-widest uppercase">API defender DashBoard</span>
                </div>
              </div>
              <div className="flex items-center gap-3 flex-wrap">
                <div className="bg-white/10 rounded-xl px-4 py-2 text-sm border border-white/20 mono">
                </div>
              </div>
            </div>
          </div>


      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {/* {stats.map((stat, i) => (
          <div key={i} className="stat-card">
            <div className="flex items-start justify-between mb-3">
              <div className={`w-10 h-10 ${stat.bg} rounded-xl flex items-center justify-center text-xl`}>{stat.icon}</div>
              <span className={`${stat.tc} text-2xl font-bold`}>{stat.val}</span>
            </div>
            <div className="text-gray-800 font-semibold text-sm">{stat.label}</div>
            <div className="text-gray-400 text-xs mt-0.5">{stat.sub}</div>
          </div>
        ))} */}
      </div>

      <div className="glass-card rounded-2xl shadow-md overflow-hidden bg-slate-300 ">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-6 py-4 border-b border-indigo-50">
          <h2 className="text-gray-800 font-semibold text-lg">All Endpoints</h2>
          <div className="flex items-center gap-3 flex-wrap">
            <input type="text" placeholder="Search APIs…" value={search} onChange={(e) => setSearch(e.target.value)}
              className="border border-indigo-100 rounded-xl px-4 py-2 text-sm text-gray-600 bg-white w-48 transition"/>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-indigo-100 rounded-xl pl-3 pr-6 py-2 text-sm text-gray-600 bg-white transition">
              <option value="all">All Status</option>
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
              <option value="Danger">Danger</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-indigo-50/70 text-indigo-800 text-xs uppercase tracking-wider">
                <th className="text-left px-6 py-4 font-semibold rounded-tl-xl">S.No</th>
                <th className="text-left px-6 py-4 font-semibold">API Name</th>
                <th className="text-left px-6 py-4 font-semibold">Last Hit</th>
                <th className="text-left px-6 py-4 font-semibold">Security Score</th>
                <th className="text-left px-6 py-4 font-semibold">Method</th>
                <th className="text-left px-6 py-4 font-semibold rounded-tr-xl">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-indigo-50/80">
              {filteredAPIs.map((api, i) => {
                const badge = getBadge(api.status);
                const rowClass = "hover:bg-indigo-50 cursor-pointer duration-200 font-semibold text-gray-800";
                return (
                  <tr 
                    key={i} 
                    className={`row-in ${rowClass}`} 
                    onClick={() => fetchAPIAnalysis(api.apiKey, api.name)}
                    style={{animationDelay: `${i*35}ms`}}
                  >
                    <td className="px-6 py-4 text-gray-600 mono text-xs">{String(i+1).padStart(2,"0")}</td>
                    <td className="px-6 py-4 font-semibold text-gray-800">{api.name}</td>
                    <td className="px-6 py-4 text-gray-400 text-xs">{api.hit}</td>
                    <td className="px-6 py-4">
                      <div className={`flex items-center gap-2 ${SC(api.score)}`}>
                        <div className="score-bar-wrap"><div className="score-bar" style={{width:`${api.score}%`}}></div></div>
                        <span className="snum mono text-xs font-semibold">{api.score}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`mono text-xs font-semibold px-3 py-1 rounded-lg ${MC[api.method]||"bg-gray-100 text-gray-600"}`}>{api.method}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={badge.className}>
                        <span className={badge.dotClassName}></span>
                        {badge.text}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filteredAPIs.length === 0 && (
            <div className="py-16 text-center text-gray-400 text-sm">No APIs match your filters.</div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-indigo-50 flex justify-between items-center text-xs text-gray-400">
          <span>{filteredAPIs.length === apis.length ? 'Showing all results' : `Showing ${filteredAPIs.length} of ${apis.length} APIs`}</span>
          <span className="mono text-indigo-300">v2.4.1</span>
        </div>
      </div>

      {/* Security Analysis Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-4xl w-full my-8 shadow-2xl">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-6 text-white flex justify-between items-start rounded-t-2xl">
              <div>
                <h3 className="text-2xl font-bold mb-2">{selectedAPI}</h3>
                <p className="text-indigo-100 text-sm">Security Analysis Report</p>
              </div>
              <button 
                onClick={closeModal}
                className="text-white hover:bg-white/20 rounded-lg p-2 transition"
              >
                ✕
              </button>
            </div>

            {/* Modal Content */}
            <div className="px-6 py-6">
              {loading && (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-4"></div>
                  <p className="text-gray-600 text-sm">Analyzing API security...</p>
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
                  ⚠️ Error: {error}
                </div>
              )}

              {!loading && !error && analysisData && (
                <div className="space-y-6">
                  {/* Security Score Section */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-gradient-to-br from-indigo-50 to-blue-50 p-6 rounded-xl border border-indigo-100">
                      <p className="text-gray-600 text-sm font-semibold mb-3">Security Score</p>
                      <div className="flex items-end gap-4">
                        <div className="text-5xl font-bold text-indigo-600">{analysisData.security_score}</div>
                        <div className="mb-2">
                          <p className="text-xs text-gray-500">out of 100</p>
                          <span className={`inline-block px-3 py-1 rounded-lg text-xs font-semibold ${getSeverityBadge(analysisData.severity)} border`}>
                            {analysisData.severity} Risk
                          </span>
                        </div>
                      </div>
                      <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all ${
                            analysisData.security_score >= 80 ? 'bg-green-500' :
                            analysisData.security_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{width: `${analysisData.security_score}%`}}
                        ></div>
                      </div>
                    </div>

                    {/* Endpoint Info */}
                    <div className="bg-gradient-to-br from-violet-50 to-purple-50 p-6 rounded-xl border border-violet-100">
                      <p className="text-gray-600 text-sm font-semibold mb-3">API Endpoint</p>
                      <code className="text-sm text-violet-700 bg-white px-3 py-2 rounded border border-violet-200 block mb-3 break-all">
                        {analysisData.endpoint}
                      </code>
                      <div className="text-xs text-gray-500">
                        <p>🔗 Full Endpoint Path</p>
                      </div>
                    </div>
                  </div>

                  {/* Source Code Section */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-800 mb-3">📝 Original Source Code</h4>
                    <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                      <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap break-words">
                        {analysisData.source_code}
                      </pre>
                    </div>
                  </div>

                  {/* Suggested Code (if needs improvement) */}
                  {analysisData.needs_improvement && analysisData.suggested_code && (
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-lg">💡</span>
                        <h4 className="text-sm font-semibold text-gray-800">Suggested Secure Code</h4>
                        <span className={`ml-auto px-3 py-1 rounded-lg text-xs font-semibold ${getSeverityBadge(analysisData.severity)} border`}>
                          Security Score Below Threshold
                        </span>
                      </div>
                      <div className="bg-green-50 rounded-lg p-4 overflow-x-auto border border-green-200">
                        <pre className="text-xs text-green-900 font-mono whitespace-pre-wrap break-words">
                          {analysisData.suggested_code}
                        </pre>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        👆 Use this improved version to enhance your API security.
                      </p>
                    </div>
                  )}

                  {!analysisData.needs_improvement && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800 text-sm">
                      ✅ This API meets security standards. No improvements suggested at this time.
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 rounded-b-2xl flex justify-end gap-3">
              <button 
                onClick={closeModal}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg text-sm font-semibold transition"
              >
                Close
              </button>
              {analysisData?.suggested_code && (
                <button 
                  onClick={() => {
                    navigator.clipboard.writeText(analysisData.suggested_code);
                    alert('Suggested code copied to clipboard!');
                  }}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition"
                >
                  📋 Copy Suggested Code
                </button>
              )}
            </div>
          </div>
        </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;
