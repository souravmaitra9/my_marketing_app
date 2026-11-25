import { useEffect, useState } from "react";

import { request } from "../api";
import { splitList } from "../format";

const emptyRules = {
  name: "",
  description: "",
  industries: "",
  regions: "",
  tags_any: "",
  employee_bands: "",
};

const emptyContact = {
  email: "",
  name: "",
  company: "",
  industry: "",
  region: "",
  employee_band: "",
  tags: "",
};

export function Segments() {
  const [segments, setSegments] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [form, setForm] = useState(emptyRules);
  const [contact, setContact] = useState(emptyContact);
  const [match, setMatch] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    const [segmentPage, contactPage] = await Promise.all([
      request("/api/segments?limit=200"),
      request("/api/contacts?limit=200"),
    ]);
    setSegments(segmentPage.items);
    setContacts(contactPage.items);
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

  function saveSegment(event) {
    event.preventDefault();
    return run(async () => {
      await request("/api/segments", {
        method: "POST",
        body: JSON.stringify({
          name: form.name,
          description: form.description,
          rules: {
            industries: splitList(form.industries),
            regions: splitList(form.regions),
            tags_any: splitList(form.tags_any),
            employee_bands: splitList(form.employee_bands),
          },
        }),
      });
      setForm(emptyRules);
      setMatch(null);
      await load();
    });
  }

  function saveContact(event) {
    event.preventDefault();
    return run(async () => {
      await request("/api/contacts", {
        method: "POST",
        body: JSON.stringify({
          email: contact.email,
          name: contact.name,
          company: contact.company,
          industry: contact.industry,
          region: contact.region,
          employee_band: contact.employee_band,
          tags: splitList(contact.tags),
        }),
      });
      setContact(emptyContact);
      await load();
    });
  }

  function preview(segment) {
    return run(async () => {
      const result = await request(`/api/segments/${segment.id}/match`, { method: "POST" });
      setMatch({ name: segment.name, ...result });
    });
  }

  function removeContact(id) {
    return run(async () => {
      await request(`/api/contacts/${id}`, { method: "DELETE" });
      await load();
    });
  }

  return (
    <section>
      <header className="bar">
        <div>
          <h1>Audience</h1>
          <p className="lede">Rules are AND across fields and OR inside a field. Empty rules match everyone.</p>
        </div>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <div className="split">
        <form className="panel stack" onSubmit={saveSegment}>
          <h2>Segment</h2>
          <label>
            Name
            <input
              required
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </label>
          <label>
            Description
            <input
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
          </label>
          <label>
            Industries
            <input
              placeholder="food, retail"
              value={form.industries}
              onChange={(event) => setForm({ ...form, industries: event.target.value })}
            />
          </label>
          <label>
            Regions
            <input
              placeholder="city, county"
              value={form.regions}
              onChange={(event) => setForm({ ...form, regions: event.target.value })}
            />
          </label>
          <label>
            Tags, any
            <input
              placeholder="loyalty, wholesale"
              value={form.tags_any}
              onChange={(event) => setForm({ ...form, tags_any: event.target.value })}
            />
          </label>
          <label>
            Employee bands
            <input
              placeholder="1-10, 11-50"
              value={form.employee_bands}
              onChange={(event) => setForm({ ...form, employee_bands: event.target.value })}
            />
          </label>
          <div className="actions">
            <button type="submit" className="primary" disabled={busy}>
              Save segment
            </button>
          </div>
          {segments.length === 0 ? <p className="empty">No segments yet.</p> : null}
          <ul className="plain">
            {segments.map((segment) => (
              <li key={segment.id}>
                <div>
                  <strong>{segment.name}</strong>
                  <p>{segment.description || "No description"}</p>
                </div>
                <button type="button" disabled={busy} onClick={() => preview(segment)}>
                  Preview
                </button>
              </li>
            ))}
          </ul>
          {match ? (
            <p className="match">
              {match.name}: {match.count} contact{match.count === 1 ? "" : "s"}
              {match.sample.length
                ? ` (${match.sample.map((item) => item.name).join(", ")})`
                : ""}
            </p>
          ) : null}
        </form>
        <form className="panel stack" onSubmit={saveContact}>
          <h2>Contacts</h2>
          <label>
            Name
            <input
              required
              value={contact.name}
              onChange={(event) => setContact({ ...contact, name: event.target.value })}
            />
          </label>
          <label>
            Email
            <input
              required
              type="email"
              value={contact.email}
              onChange={(event) => setContact({ ...contact, email: event.target.value })}
            />
          </label>
          <div className="fields">
            <label>
              Company
              <input
                value={contact.company}
                onChange={(event) => setContact({ ...contact, company: event.target.value })}
              />
            </label>
            <label>
              Industry
              <input
                value={contact.industry}
                onChange={(event) => setContact({ ...contact, industry: event.target.value })}
              />
            </label>
          </div>
          <div className="fields">
            <label>
              Region
              <input
                value={contact.region}
                onChange={(event) => setContact({ ...contact, region: event.target.value })}
              />
            </label>
            <label>
              Band
              <input
                placeholder="1-10"
                value={contact.employee_band}
                onChange={(event) => setContact({ ...contact, employee_band: event.target.value })}
              />
            </label>
          </div>
          <label>
            Tags
            <input
              placeholder="loyalty, wholesale"
              value={contact.tags}
              onChange={(event) => setContact({ ...contact, tags: event.target.value })}
            />
          </label>
          <div className="actions">
            <button type="submit" className="primary" disabled={busy}>
              Add contact
            </button>
          </div>
          {contacts.length === 0 ? <p className="empty">No contacts yet.</p> : null}
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Industry</th>
                <th>Region</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {contacts.map((item) => (
                <tr key={item.id}>
                  <td>
                    {item.name}
                    <div className="sub">{item.email}</div>
                  </td>
                  <td>{item.industry || "-"}</td>
                  <td>{item.region || "-"}</td>
                  <td>
                    <button type="button" disabled={busy} onClick={() => removeContact(item.id)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </form>
      </div>
    </section>
  );
}
