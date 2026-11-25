import { useEffect, useState } from "react";

import { request } from "../api";
import { defaultSchedule, providerLabel } from "../format";

const CHANNELS = ["instagram", "linkedin", "facebook", "email"];
const OBJECTIVES = ["awareness", "conversion", "retention"];
const STATUSES = ["draft", "active", "paused", "completed"];

function emptyForm() {
  return {
    name: "",
    channel: "instagram",
    objective: "awareness",
    status: "draft",
    brief: "",
    segment_id: "",
  };
}

export function Campaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [segments, setSegments] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [drafts, setDrafts] = useState([]);
  const [gen, setGen] = useState({ kind: "social", tone: "direct", variants: "2" });
  const [post, setPost] = useState({ subject: "", body: "", scheduled_for: defaultSchedule() });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    const [campaignPage, segmentPage] = await Promise.all([
      request("/api/campaigns"),
      request("/api/segments?limit=200"),
    ]);
    setCampaigns(campaignPage.items);
    setSegments(segmentPage.items);
    return campaignPage.items;
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  function patchForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function openCampaign(id) {
    setError("");
    setCreating(false);
    setSelectedId(id);
    const [campaign, rows] = await Promise.all([
      request(`/api/campaigns/${id}`),
      request(`/api/campaigns/${id}/drafts`),
    ]);
    setForm({
      name: campaign.name,
      channel: campaign.channel,
      objective: campaign.objective,
      status: campaign.status,
      brief: campaign.brief,
      segment_id: campaign.segment_id || "",
    });
    setDrafts(rows);
    setPost({ subject: "", body: "", scheduled_for: defaultSchedule() });
  }

  function startCreate() {
    setCreating(true);
    setSelectedId(null);
    setDrafts([]);
    setForm(emptyForm());
    setError("");
  }

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

  function save() {
    const payload = {
      name: form.name,
      channel: form.channel,
      objective: form.objective,
      status: form.status,
      brief: form.brief,
      segment_id: form.segment_id || null,
    };
    return run(async () => {
      if (creating || !selectedId) {
        const created = await request("/api/campaigns", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        await load();
        await openCampaign(created.id);
        return;
      }
      await request(`/api/campaigns/${selectedId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      await load();
    });
  }

  function remove() {
    if (!selectedId || !window.confirm("Delete this campaign and its queued posts?")) {
      return;
    }
    return run(async () => {
      await request(`/api/campaigns/${selectedId}`, { method: "DELETE" });
      setSelectedId(null);
      setCreating(false);
      setDrafts([]);
      setForm(emptyForm());
      await load();
    });
  }

  function generate() {
    if (!selectedId) {
      return;
    }
    return run(async () => {
      await request(`/api/campaigns/${selectedId}/generate`, {
        method: "POST",
        body: JSON.stringify({
          kind: gen.kind,
          tone: gen.tone,
          variants: Number(gen.variants),
        }),
      });
      setDrafts(await request(`/api/campaigns/${selectedId}/drafts`));
    });
  }

  function useDraft(draft) {
    setPost((current) => ({
      ...current,
      subject: draft.subject || "",
      body: draft.body,
    }));
  }

  function schedule() {
    if (!selectedId) {
      return;
    }
    return run(async () => {
      await request("/api/posts", {
        method: "POST",
        body: JSON.stringify({
          campaign_id: selectedId,
          channel: form.channel,
          subject: post.subject,
          body: post.body,
          scheduled_for: new Date(post.scheduled_for).toISOString(),
        }),
      });
      setPost({ subject: "", body: "", scheduled_for: defaultSchedule() });
    });
  }

  const showEditor = creating || selectedId;

  return (
    <section>
      <header className="bar">
        <div>
          <h1>Campaigns</h1>
          <p className="lede">A brief, a channel, and the copy you are willing to send.</p>
        </div>
        <button type="button" className="primary" onClick={startCreate}>
          New campaign
        </button>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <div className="split">
        <div className="panel">
          {campaigns.length === 0 ? (
            <p className="empty">No campaigns yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Channel</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((campaign) => (
                  <tr
                    key={campaign.id}
                    className={campaign.id === selectedId ? "selected" : ""}
                    tabIndex={0}
                    onClick={() => openCampaign(campaign.id).catch((err) => setError(err.message))}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        openCampaign(campaign.id).catch((err) => setError(err.message));
                      }
                    }}
                  >
                    <td>{campaign.name}</td>
                    <td>{campaign.channel}</td>
                    <td>
                      <span className={`pill ${campaign.status}`}>{campaign.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        {showEditor ? (
          <div className="panel stack">
            <label>
              Name
              <input value={form.name} onChange={(event) => patchForm("name", event.target.value)} />
            </label>
            <div className="fields">
              <label>
                Channel
                <select value={form.channel} onChange={(event) => patchForm("channel", event.target.value)}>
                  {CHANNELS.map((channel) => (
                    <option key={channel} value={channel}>
                      {channel}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Objective
                <select
                  value={form.objective}
                  onChange={(event) => patchForm("objective", event.target.value)}
                >
                  {OBJECTIVES.map((objective) => (
                    <option key={objective} value={objective}>
                      {objective}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Status
                <select value={form.status} onChange={(event) => patchForm("status", event.target.value)}>
                  {STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              Audience
              <select
                value={form.segment_id}
                onChange={(event) => patchForm("segment_id", event.target.value)}
              >
                <option value="">No segment</option>
                {segments.map((segment) => (
                  <option key={segment.id} value={segment.id}>
                    {segment.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Brief
              <textarea
                rows="4"
                value={form.brief}
                onChange={(event) => patchForm("brief", event.target.value)}
                placeholder="What is true, and what should the copy not invent?"
              />
            </label>
            <div className="actions">
              <button type="button" className="primary" disabled={busy} onClick={save}>
                Save
              </button>
              {selectedId ? (
                <button type="button" className="danger" disabled={busy} onClick={remove}>
                  Delete
                </button>
              ) : null}
            </div>
            {selectedId ? (
              <>
                <h2>Draft copy</h2>
                <div className="fields">
                  <label>
                    Kind
                    <select value={gen.kind} onChange={(event) => setGen({ ...gen, kind: event.target.value })}>
                      <option value="social">social</option>
                      <option value="email">email</option>
                    </select>
                  </label>
                  <label>
                    Tone
                    <select value={gen.tone} onChange={(event) => setGen({ ...gen, tone: event.target.value })}>
                      <option value="direct">direct</option>
                      <option value="warm">warm</option>
                      <option value="formal">formal</option>
                    </select>
                  </label>
                  <label>
                    Variants
                    <select
                      value={gen.variants}
                      onChange={(event) => setGen({ ...gen, variants: event.target.value })}
                    >
                      <option value="1">1</option>
                      <option value="2">2</option>
                      <option value="3">3</option>
                    </select>
                  </label>
                </div>
                <div className="actions">
                  <button type="button" disabled={busy} onClick={generate}>
                    Write drafts
                  </button>
                </div>
                {drafts.length === 0 ? <p className="empty">No drafts yet.</p> : null}
                <ul className="drafts">
                  {drafts.map((draft) => (
                    <li key={draft.id}>
                      <div className="draft-meta">
                        <span>{draft.kind}</span>
                        <span>{draft.tone}</span>
                        <span>{providerLabel(draft.provider)}</span>
                      </div>
                      {draft.subject ? <strong>{draft.subject}</strong> : null}
                      <p>{draft.body}</p>
                      <button type="button" onClick={() => useDraft(draft)}>
                        Use in queue
                      </button>
                    </li>
                  ))}
                </ul>
                <h2>Schedule</h2>
                <label>
                  Subject
                  <input
                    value={post.subject}
                    onChange={(event) => setPost({ ...post, subject: event.target.value })}
                  />
                </label>
                <label>
                  Body
                  <textarea
                    rows="4"
                    value={post.body}
                    onChange={(event) => setPost({ ...post, body: event.target.value })}
                  />
                </label>
                <label>
                  When
                  <input
                    type="datetime-local"
                    value={post.scheduled_for}
                    onChange={(event) => setPost({ ...post, scheduled_for: event.target.value })}
                  />
                </label>
                <div className="actions">
                  <button type="button" className="primary" disabled={busy || !post.body.trim()} onClick={schedule}>
                    Queue post
                  </button>
                </div>
              </>
            ) : null}
          </div>
        ) : (
          <div className="panel">
            <p className="empty">Select a campaign or start a new one.</p>
          </div>
        )}
      </div>
    </section>
  );
}
