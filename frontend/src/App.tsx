import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("Checking backend...");

  useEffect(() => {
    fetch("http://localhost:8000/api/health")
      .then((res) => res.json())
      .then((data) => setStatus(data.message))
      .catch(() => setStatus("Backend not reachable"));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow p-8 text-center">
        <h1 className="text-3xl font-bold text-teal-700">MediLens AI</h1>
        <p className="mt-2 text-slate-600">
          Explainable medical report analyzer
        </p>
        <p className="mt-4 text-sm text-slate-500">{status}</p>
      </div>
    </div>
  );
}

export default App;