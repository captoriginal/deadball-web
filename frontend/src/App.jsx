import { useMemo } from "react";

const sampleRequest = {
  mode: "season",
  payload: "https://example.com/mlb-2023.csv",
};

export default function App() {
  const prettyRequest = useMemo(
    () => JSON.stringify(sampleRequest, null, 2),
    []
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <header className="mb-10 space-y-3">
          <p className="text-sm uppercase tracking-wide text-indigo-500">
            Deadball Web
          </p>
          <h1 className="text-3xl font-semibold sm:text-4xl">
            Generate Deadball rosters from MLB data.
          </h1>
          <p className="text-slate-600 sm:text-lg">
            Frontend scaffold is ready. Point VITE_API_BASE_URL at the FastAPI
            backend and start wiring up the generate flow.
          </p>
        </header>

        <section className="grid gap-6 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white/60 p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-800">Next steps</h2>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              <li>1) Create a simple form to choose mode and paste a URL/CSV.</li>
              <li>2) Call the backend `/api/generate` endpoint.</li>
              <li>3) Render roster + players in a clean table or cards.</li>
            </ul>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-900 p-6 text-slate-50 shadow-sm">
            <h2 className="text-lg font-semibold">Sample request</h2>
            <pre className="mt-4 whitespace-pre-wrap break-words text-sm leading-6">
              {prettyRequest}
            </pre>
          </div>
        </section>
      </div>
    </div>
  );
}
