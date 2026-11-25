import { useEffect, useRef, useState } from "react";

import { request } from "../api";
import { formatWhen } from "../format";

const FILTERS = ["", "queued", "sending", "sent", "failed", "cancelled"];

export function Queue() {
  const [status, setStatus] = useState("queued");
  const [posts, setPosts] = useState([]);
  const [campaigns, setCampaigns] = useState({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const loadSeq = useRef(0);

  async function load(nextStatus = status) {
    const seq = ++loadSeq.current;
    const params = new URLSearchParams({ limit: "200" });
    if (nextStatus) {
      params.set("status", nextStatus);
    }
    const [postPage, campaignPage] = await Promise.all([
      request(`/api/posts?${params.toString()}`),
      request("/api/campaigns?limit=200"),
    ]);
    if (seq !== loadSeq.current) {
      return;
    }
    const names = {};
    for (const campaign of campaignPage.items) {
      names[campaign.id] = campaign.name;
    }
    setCampaigns(names);
    setPosts(postPage.items);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  async function run(action) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function changeFilter(value) {
    setStatus(value);
    run(() => load(value));
  }

  function cancel(id) {
    run(async () => {
      await request(`/api/posts/${id}/cancel`, { method: "POST" });
      await load();
    });
  }

  function retry(id) {
    run(async () => {
      await request(`/api/posts/${id}/retry`, { method: "POST" });
      await load();
    });
  }

  return (
    <section>
      <header className="bar">
        <div>
          <h1>Queue</h1>
          <p className="lede">Postgres holds the posts. The worker locks a row in Redis, then marks it sent.</p>
        </div>
        <label className="inline">
          Status
          <select value={status} onChange={(event) => changeFilter(event.target.value)}>
            {FILTERS.map((item) => (
              <option key={item || "all"} value={item}>
                {item || "all"}
              </option>
            ))}
          </select>
        </label>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <div className="panel">
        {posts.length === 0 ? <p className="empty">Nothing in this view.</p> : null}
        {posts.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Campaign</th>
                <th>Channel</th>
                <th>Status</th>
                <th>Copy</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {posts.map((post) => (
                <tr key={post.id}>
                  <td>{formatWhen(post.scheduled_for)}</td>
                  <td>{campaigns[post.campaign_id] || post.campaign_id.slice(0, 8)}</td>
                  <td>{post.channel}</td>
                  <td>
                    <span className={`pill ${post.status}`}>{post.status}</span>
                    {post.last_error ? <div className="sub">{post.last_error}</div> : null}
                  </td>
                  <td className="copy">{post.body}</td>
                  <td>
                    {post.status === "queued" ? (
                      <button type="button" disabled={busy} onClick={() => cancel(post.id)}>
                        Cancel
                      </button>
                    ) : null}
                    {post.status === "failed" || post.status === "sending" ? (
                      <button type="button" disabled={busy} onClick={() => retry(post.id)}>
                        Retry
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>
    </section>
  );
}
