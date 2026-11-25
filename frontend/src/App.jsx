import { useEffect, useState } from "react";

import { request } from "./api";
import { Campaigns } from "./views/Campaigns";
import { Queue } from "./views/Queue";
import { Segments } from "./views/Segments";

const VIEWS = [
  ["campaigns", "Campaigns"],
  ["segments", "Audience"],
  ["queue", "Queue"],
];

export function App() {
  const [view, setView] = useState("campaigns");
  const [ready, setReady] = useState(null);

  useEffect(() => {
    request("/api/campaigns?limit=1")
      .then(() => setReady(true))
      .catch(() => setReady(false));
  }, []);

  let status = "Checking the API";
  if (ready === true) {
    status = "API ready";
  } else if (ready === false) {
    status = "API unreachable";
  }

  return (
    <div className="shell">
      <aside className="side">
        <div className="mark">
          <span className="mark-name">Leaflet</span>
          <span className="mark-note">Campaign desk</span>
        </div>
        <nav className="nav">
          {VIEWS.map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={view === id ? "nav-btn on" : "nav-btn"}
              onClick={() => setView(id)}
            >
              {label}
            </button>
          ))}
        </nav>
        <p className={ready ? "side-status ok" : "side-status"}>{status}</p>
      </aside>
      <main className="main">
        {view === "campaigns" ? <Campaigns /> : null}
        {view === "segments" ? <Segments /> : null}
        {view === "queue" ? <Queue /> : null}
      </main>
    </div>
  );
}
