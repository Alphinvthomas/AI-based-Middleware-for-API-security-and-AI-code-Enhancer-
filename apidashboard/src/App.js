import { useState, useEffect } from 'react';

const MC = {
  GET:"bg-blue-50 text-blue-600",
  POST:"bg-violet-50 text-violet-600",
  PUT:"bg-amber-50 text-amber-600"
};

const SC = s => s>=80?"text-green-600":s>=60?"text-yellow-600":"text-red-600";

const getBadge = (s) => {
  const map = {
    Active:"bg-green-100 text-green-700",
    Inactive:"bg-gray-100 text-gray-600",
    Danger:"bg-red-100 text-red-700"
  };
  return map[s] || map.Inactive;
};

function App() {

  const [apis, setApis] = useState([]);
  const [apisLoading, setApisLoading] = useState(true);

  const [analysisData, setAnalysisData] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // 🚀 Fetch APIs from backend
  useEffect(() => {
    setApisLoading(true);

    fetch('http://localhost:5000/api/list')
      .then(res => res.json())
      .then(data => {
        if (data.apis && Array.isArray(data.apis)) {
          const transformedApis = data.apis.map(api => ({
            name: api.name,
            apiKey: api.apiKey,
            ep: api.endpoint,
            method: api.method,
            score: api.score !== undefined ? api.score : "—",
            status: api.status || "Active",
            hit: "Just now"
          }));
          setApis(transformedApis);
        } else {
          setApis([]);
        }
        setApisLoading(false);
      })
      .catch(() => {
        setApis([]);
        setApisLoading(false);
      });
  }, []);

  // 🔍 Fetch Analysis
  const fetchAPIAnalysis = async (apiKey) => {
    setLoading(true);
    setShowModal(true);

    try {
      const res = await fetch(`http://localhost:5000/api/analyze/${apiKey}`);
      const data = await res.json();
      setAnalysisData(data);
    } catch {
      setAnalysisData({ error: "Failed to load" });
    } finally {
      setLoading(false);
    }
  };

  // 🧱 Skeleton Row
  const SkeletonRow = () => (
    <tr className="animate-pulse">
      {[...Array(4)].map((_, i) => (
        <td key={i} className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded"></div>
        </td>
      ))}
    </tr>
  );

  return (
    <div className="p-6">

      <h1 className="text-2xl font-bold mb-4">API Dashboard</h1>

      <table className="w-full bg-white rounded-xl overflow-hidden shadow">
        <thead className="bg-gray-100 text-sm">
          <tr>
            <th className="p-3 text-left">Name</th>
            <th className="p-3">Score</th>
            <th className="p-3">Method</th>
            <th className="p-3">Status</th>
          </tr>
        </thead>

        <tbody>
          {apisLoading ? (
            [...Array(5)].map((_, i) => <SkeletonRow key={i} />)
          ) : (
            apis.map((api, i) => (
              <tr
                key={i}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => fetchAPIAnalysis(api.apiKey)}
              >
                <td className="p-3">{api.name}</td>

                <td className={`p-3 font-bold ${SC(api.score)}`}>
                  {api.score}
                </td>

                <td className="p-3">
                  <span className={`px-2 py-1 rounded text-xs ${MC[api.method]}`}>
                    {api.method}
                  </span>
                </td>

                <td className="p-3">
                  <span className={`px-2 py-1 text-xs rounded ${getBadge(api.status)}`}>
                    {api.status}
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* 🔍 Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
          <div className="bg-white p-6 rounded-xl w-[600px]">

            {loading ? (
              <p>Analyzing...</p>
            ) : (
              <>
                <h2 className="text-xl font-bold mb-3">Security Report</h2>

                {analysisData?.error ? (
                  <p className="text-red-500">{analysisData.error}</p>
                ) : (
                  <>
                    <p><b>Score:</b> {analysisData?.security_score}</p>

                    <pre className="bg-gray-900 text-white p-3 mt-3 rounded text-xs overflow-auto">
                      {analysisData?.source_code}
                    </pre>

                    {analysisData?.suggested_code && (
                      <pre className="bg-green-100 p-3 mt-3 rounded text-xs overflow-auto">
                        {analysisData.suggested_code}
                      </pre>
                    )}
                  </>
                )}
              </>
            )}

            <button
              onClick={() => setShowModal(false)}
              className="mt-4 px-4 py-2 bg-gray-300 rounded"
            >
              Close
            </button>

          </div>
        </div>
      )}

    </div>
  );
}

export default App;