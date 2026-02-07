function lncGetToken() {
  return localStorage.getItem("lnc_token") || "";
}

function lncPromptToken() {
  const current = lncGetToken();
  const next = prompt("Local Nexus token (optional). Leave empty to clear.", current);
  if (next === null) return;
  if (next.trim() === "") {
    localStorage.removeItem("lnc_token");
    alert("Token cleared.");
    return;
  }
  localStorage.setItem("lnc_token", next.trim());
  alert("Token saved to localStorage.");
}

async function lncFetchJson(url, options = {}) {
  const headers = options.headers || {};
  const token = lncGetToken();
  if (token) headers["X-Local-Nexus-Token"] = token;
  if (!headers["Content-Type"] && options.body) headers["Content-Type"] = "application/json";

  const res = await fetch(url, { ...options, headers });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

async function lncServiceAction(serviceId, action, reloadAfter = false) {
  try {
    await lncFetchJson(`/api/services/${serviceId}/${action}`, { method: "POST" });
    if (reloadAfter) location.reload();
  } catch (e) {
    alert(String(e.message || e));
  }
}

async function lncImportBundle() {
  const input = document.getElementById("bundle");
  const result = document.getElementById("result");
  if (!input || !result) return;

  try {
    const parsed = JSON.parse(input.value);
    const data = await lncFetchJson("/api/import/bundle", { method: "POST", body: JSON.stringify(parsed) });
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

async function lncLoadTemplate() {
  const input = document.getElementById("bundle");
  const result = document.getElementById("result");
  if (!input || !result) return;

  try {
    const data = await lncFetchJson("/api/import/bundle-template");
    input.value = JSON.stringify(data, null, 2);
    result.textContent = "Template loaded.";
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

async function lncResolvePortConflicts(reloadAfter = false) {
  try {
    const data = await lncFetchJson("/api/ports/resolve-conflicts", { method: "POST" });
    const pretty = JSON.stringify(data, null, 2);

    // If we are on Import page, show in the result panel.
    const result = document.getElementById("result");
    if (result) result.textContent = pretty;

    if (!result) {
      // Otherwise show a brief summary.
      const changes = (data && data.changes) ? data.changes.length : 0;
      const deps = (data && data.dependent_env_updates) ? data.dependent_env_updates.length : 0;
      alert(`Resolved ports.\nChanges: ${changes}\nDependent env updates: ${deps}`);
    }

    if (reloadAfter) location.reload();
  } catch (e) {
    alert(String(e.message || e));
  }
}
