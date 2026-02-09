function lncGetToken() {
  return localStorage.getItem("lnc_token") || "";
}

function lncGetGitHubToken() {
  return localStorage.getItem("lnc_github_token") || "";
}

let lncGitHubReposCache = [];
let lncGitHubSelectedRepoFullName = "";
let lncLastPr = null; // { repo: "owner/repo", branch: "branch-name", pr_url: "..." }

function lncParsePrimitive(arg) {
  const s = String(arg || "").trim();
  if (s === "") return undefined;
  if (s === "true") return true;
  if (s === "false") return false;
  if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);
  // quoted string (single or double)
  const m = s.match(/^(['"])([\s\S]*)\1$/);
  if (m) return m[2];
  return undefined;
}

function lncBindInlineHandlers() {
  // Some environments block inline onclick handlers; bind them programmatically.
  const els = document.querySelectorAll("[onclick]");
  for (const el of els) {
    const raw = el.getAttribute("onclick");
    if (!raw) continue;
    // Only take over simple function-call handlers; leave complex inline JS alone.
    if (!raw.trim().match(/^([A-Za-z0-9_]+)\s*\(\s*([\s\S]*)\s*\)\s*;?\s*$/)) continue;
    if (el.getAttribute("data-lnc-onclick")) continue;
    el.setAttribute("data-lnc-onclick", raw);
    el.removeAttribute("onclick");
  }

  document.addEventListener(
    "click",
    (ev) => {
      const t = ev.target && ev.target.closest ? ev.target.closest("[data-lnc-onclick]") : null;
      if (!t) return;
      const raw = t.getAttribute("data-lnc-onclick") || "";
      const m = raw.trim().match(/^([A-Za-z0-9_]+)\s*\(\s*([\s\S]*)\s*\)\s*;?\s*$/);
      if (!m) return;
      const fnName = m[1];
      const argsRaw = (m[2] || "").trim();
      const fn = window[fnName];
      if (typeof fn !== "function") return;

      let args = [];
      if (argsRaw !== "") {
        // Support a small subset of args used in this app: booleans, numbers, simple strings.
        args = argsRaw
          .split(",")
          .map((a) => lncParsePrimitive(a))
          .filter((a) => a !== undefined);
      }

      try {
        fn(...args);
      } catch (e) {
        const result = document.getElementById("result");
        if (result) result.textContent = String((e && e.message) || e);
      }
    },
    true
  );
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", lncBindInlineHandlers);
} else {
  lncBindInlineHandlers();
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

function lncPromptGitHubToken() {
  const current = lncGetGitHubToken();
  const next = prompt("GitHub token (PAT) for importing private repos (optional). Leave empty to clear.", current);
  if (next === null) return;
  if (next.trim() === "") {
    localStorage.removeItem("lnc_github_token");
    alert("GitHub token cleared.");
    return;
  }
  localStorage.setItem("lnc_github_token", next.trim());
  alert("GitHub token saved to localStorage.");
}

function lncSleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function lncEscapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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

async function lncConnectGitHubMobile() {
  const result = document.getElementById("result");
  if (!result) return;

  try {
    const start = await lncFetchJson("/api/import/github-device-start", {
      method: "POST",
      body: JSON.stringify({ scope: "repo" }),
    });

    const verificationUri = start && start.verification_uri ? String(start.verification_uri) : "";
    const userCode = start && start.user_code ? String(start.user_code) : "";
    const deviceCode = start && start.device_code ? String(start.device_code) : "";
    const intervalSec = Math.max(3, Number((start && start.interval) || 5));
    const expiresInSec = Math.max(30, Number((start && start.expires_in) || 900));

    if (!verificationUri || !userCode || !deviceCode) {
      result.textContent = `Unexpected device auth response:\n${JSON.stringify(start, null, 2)}`;
      return;
    }

    // Best-effort: copy code for easy paste into GitHub page.
    let copied = false;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(userCode);
        copied = true;
      }
    } catch {
      // ignore
    }

    result.textContent =
      `GitHub mobile auth started.\n\n` +
      `1) Open: ${verificationUri}\n` +
      `2) Enter code on GitHub: ${userCode}${copied ? " (copied to clipboard)" : ""}\n` +
      `3) Approve in GitHub (mobile/2FA)\n\n` +
      `Waiting for authorization...`;

    try {
      window.open(verificationUri, "_blank", "noopener,noreferrer");
    } catch {
      // ignore
    }

    const deadline = Date.now() + expiresInSec * 1000;
    let nextInterval = intervalSec;

    while (Date.now() < deadline) {
      await lncSleep(nextInterval * 1000);
      const poll = await lncFetchJson("/api/import/github-device-poll", {
        method: "POST",
        body: JSON.stringify({ device_code: deviceCode }),
      });

      if (poll && poll.status === "authorized" && poll.access_token) {
        localStorage.setItem("lnc_github_token", String(poll.access_token));
        result.textContent = "GitHub connected. Token saved to localStorage. You can now Load my repos / import / PR actions.";
        return;
      }

      if (poll && poll.status === "slow_down") {
        nextInterval = Math.min(nextInterval + 5, 30);
      }

      if (poll && (poll.status === "access_denied" || poll.status === "expired_token")) {
        result.textContent = `GitHub authorization failed: ${poll.status}\n${poll.error_description || ""}`.trim();
        return;
      }
    }

    result.textContent = "GitHub authorization timed out. Click “Connect GitHub (mobile)” again to restart.";
  } catch (e) {
    const msg = String((e && e.message) || e);
    if (msg.includes("LOCAL_NEXUS_GITHUB_OAUTH_CLIENT_ID")) {
      result.textContent =
        "GitHub mobile connect needs an OAuth Client ID.\n\n" +
        "1) Create a GitHub OAuth App (Settings → Developer settings → OAuth Apps).\n" +
        "2) Copy its Client ID.\n" +
        "3) Set in your .env:\n" +
        "   LOCAL_NEXUS_GITHUB_OAUTH_CLIENT_ID=<your client id>\n" +
        "4) Restart the Local Nexus Controller.\n\n" +
        `Server said: ${msg}`;
      return;
    }
    result.textContent = msg;
  }
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

async function lncImportBundlesFromFolder(dryRun) {
  const root = document.getElementById("bundleRoot");
  const includeGitReposEl = document.getElementById("includeGitRepos");
  const result = document.getElementById("result");
  if (!root || !result) return;

  const rootPath = String(root.value || "").trim();
  if (!rootPath) {
    result.textContent = "Enter a folder path first (e.g. C:/Users/you/source/repos).";
    return;
  }

  try {
    const includeGitRepos = includeGitReposEl ? !!includeGitReposEl.checked : true;
    const payload = { root: rootPath, dry_run: !!dryRun, include_git_repos: includeGitRepos };
    const data = await lncFetchJson("/api/import/scan-bundles", { method: "POST", body: JSON.stringify(payload) });
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

function lncFillGitHubDefaults() {
  const repo = document.getElementById("ghRepo");
  const ref = document.getElementById("ghRef");
  const path = document.getElementById("ghPath");
  if (ref && String(ref.value || "").trim() === "") ref.value = "main";
  if (path && String(path.value || "").trim() === "") path.value = "local-nexus.bundle.json";
  if (repo && String(repo.value || "").trim() === "") repo.focus();
}

function lncRenderGitHubRepos(repos) {
  const browser = document.getElementById("ghRepoBrowser");
  const list = document.getElementById("ghRepoList");
  const count = document.getElementById("ghRepoCount");
  if (!browser || !list || !count) return;

  browser.classList.remove("hidden");
  count.textContent = String((repos || []).length);

  const items = (repos || []).map((r) => {
    const name = lncEscapeHtml(r.full_name || "");
    const desc = lncEscapeHtml(r.description || "");
    const meta = [
      r.private ? "private" : "public",
      r.archived ? "archived" : "",
      r.default_branch ? `default: ${lncEscapeHtml(r.default_branch)}` : "",
    ]
      .filter(Boolean)
      .join(" • ");

    return `
      <button
        class="w-full text-left px-3 py-2 hover:bg-slate-900 border-b border-slate-800 last:border-b-0"
        data-fullname="${lncEscapeHtml(r.full_name || "")}"
      >
        <div class="flex items-center justify-between gap-3">
          <div class="font-mono text-xs text-slate-100">${name}</div>
          <div class="text-[11px] text-slate-500 shrink-0">${lncEscapeHtml(meta)}</div>
        </div>
        ${desc ? `<div class="text-xs text-slate-400 mt-1">${desc}</div>` : ""}
      </button>
    `;
  });

  list.innerHTML = items.join("") || `<div class="px-3 py-3 text-xs text-slate-400">No repos found.</div>`;

  // Wire click handlers safely (no inline JS / escaping pitfalls).
  for (const btn of list.querySelectorAll("button[data-fullname]")) {
    btn.addEventListener("click", () => {
      const fullName = btn.getAttribute("data-fullname") || "";
      lncSelectGitHubRepo(fullName);
    });
  }
}

function lncRenderGitHubBundles(bundles) {
  const browser = document.getElementById("ghBundleBrowser");
  const list = document.getElementById("ghBundleList");
  const count = document.getElementById("ghBundleCount");
  if (!browser || !list || !count) return;

  browser.classList.remove("hidden");
  count.textContent = String((bundles || []).length);

  if (!bundles || bundles.length === 0) {
    list.innerHTML = `<div class="px-3 py-3 text-xs text-slate-400">No bundles found.</div>`;
    return;
  }

  const items = bundles.map((b) => {
    const type = String(b.type || "");
    const app = b.app ? String(b.app) : "";
    const path = String(b.path || "");
    const title = type === "master" ? "Master bundle" : type === "root" ? "Root bundle" : app ? `App: ${app}` : "App bundle";
    return `
      <div class="flex items-center justify-between gap-3 px-3 py-2 border-b border-slate-800 last:border-b-0">
        <div class="min-w-0">
          <div class="text-xs text-slate-200">${lncEscapeHtml(title)}</div>
          <div class="font-mono text-[11px] text-slate-400 truncate">${lncEscapeHtml(path)}</div>
        </div>
        <button class="btn shrink-0" data-bundle-path="${lncEscapeHtml(path)}">Import</button>
      </div>
    `;
  });

  list.innerHTML = items.join("");
  for (const btn of list.querySelectorAll("button[data-bundle-path]")) {
    btn.addEventListener("click", async () => {
      const p = btn.getAttribute("data-bundle-path") || "";
      const pathEl = document.getElementById("ghPath");
      if (pathEl) pathEl.value = p;
      await lncImportFromGitHub();
    });
  }
}

async function lncLoadGitHubBundles() {
  const repoEl = document.getElementById("ghRepo");
  const refEl = document.getElementById("ghRef");
  const result = document.getElementById("result");
  if (!result) return;

  const repo = repoEl ? String(repoEl.value || "").trim() : "";
  const ref = refEl ? String(refEl.value || "").trim() : "";
  if (!repo) {
    result.textContent = "Select a GitHub repo first, then click “Load bundles”.";
    return;
  }

  const token = lncGetGitHubToken();
  if (!token) {
    result.textContent = "Set a GitHub token first (click “GitHub token”).";
    return;
  }

  try {
    const payload = { repo, ref: ref || "main", github_token: token };
    const data = await lncFetchJson("/api/import/github-list-bundles", { method: "POST", body: JSON.stringify(payload) });
    const bundles = data && data.bundles ? data.bundles : [];
    lncRenderGitHubBundles(bundles);
    result.textContent = `Found ${bundles.length} bundle(s).`;
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

function lncFilterGitHubRepos() {
  const filterEl = document.getElementById("ghRepoFilter");
  const q = filterEl ? String(filterEl.value || "").trim().toLowerCase() : "";
  if (!q) {
    lncRenderGitHubRepos(lncGitHubReposCache);
    return;
  }
  const filtered = (lncGitHubReposCache || []).filter((r) => {
    const name = String(r.full_name || "").toLowerCase();
    const desc = String(r.description || "").toLowerCase();
    return name.includes(q) || desc.includes(q);
  });
  lncRenderGitHubRepos(filtered);
}

function lncSelectGitHubRepo(fullName) {
  const repoEl = document.getElementById("ghRepo");
  const refEl = document.getElementById("ghRef");
  if (repoEl) repoEl.value = String(fullName || "").trim();
  lncGitHubSelectedRepoFullName = String(fullName || "").trim();

  const repo = (lncGitHubReposCache || []).find((r) => String(r.full_name) === String(fullName));
  if (repo && refEl && String(refEl.value || "").trim() === "") {
    refEl.value = repo.default_branch || "main";
  }
  lncFillGitHubDefaults();
}

async function lncLoadGitHubRepos() {
  const result = document.getElementById("result");
  try {
    const token = lncGetGitHubToken();
    if (!token) {
      if (result) result.textContent = "Set a GitHub token first (click “GitHub token”).";
      return;
    }
    const payload = { github_token: token, per_page: 100, max_pages: 5 };
    const data = await lncFetchJson("/api/import/github-repos", { method: "POST", body: JSON.stringify(payload) });
    lncGitHubReposCache = (data && data.repos) ? data.repos : [];
    lncRenderGitHubRepos(lncGitHubReposCache);
    if (result) result.textContent = `Loaded ${lncGitHubReposCache.length} repos from GitHub.`;
  } catch (e) {
    if (result) result.textContent = String(e.message || e);
  }
}

async function lncCreateGitHubBundlePr() {
  const repoEl = document.getElementById("ghRepo");
  const refEl = document.getElementById("ghRef");
  const pathEl = document.getElementById("ghPath");
  const needsLocalEl = document.getElementById("ghNeedsLocalSetup");
  const result = document.getElementById("result");
  if (!repoEl || !result) return;

  const repo = String(repoEl.value || "").trim();
  const ref = refEl ? String(refEl.value || "").trim() : "";
  const path = pathEl ? String(pathEl.value || "").trim() : "";
  if (!repo) {
    result.textContent = "Enter/select a GitHub repo first, then click “Create bundle PR”.";
    return;
  }

  try {
    const token = lncGetGitHubToken();
    if (!token) {
      result.textContent = "Set a GitHub token first (click “GitHub token”).";
      return;
    }
    const payload = {
      repo,
      ref: ref || "main",
      path: path || "local-nexus.bundle.json",
      github_token: token,
      needs_local_setup: needsLocalEl ? !!needsLocalEl.checked : true,
    };
    const data = await lncFetchJson("/api/import/github-create-bundle-pr", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (data && data.repo && data.branch) lncLastPr = { repo: data.repo, branch: data.branch, pr_url: data.pr_url || null };
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

async function lncCreateGitHubLocalizePr() {
  const repoEl = document.getElementById("ghRepo");
  const refEl = document.getElementById("ghRef");
  const pathEl = document.getElementById("ghPath");
  const needsLocalEl = document.getElementById("ghNeedsLocalSetup");
  const result = document.getElementById("result");
  if (!repoEl || !result) return;

  const repo = String(repoEl.value || "").trim();
  const ref = refEl ? String(refEl.value || "").trim() : "";
  const path = pathEl ? String(pathEl.value || "").trim() : "";
  if (!repo) {
    result.textContent = "Enter/select a GitHub repo first, then click “Localize PR”.";
    return;
  }

  try {
    const token = lncGetGitHubToken();
    if (!token) {
      result.textContent = "Set a GitHub token first (click “GitHub token”).";
      return;
    }

    const payload = {
      repo,
      ref: ref || "main",
      path: path || "local-nexus.bundle.json",
      github_token: token,
      needs_local_setup: needsLocalEl ? !!needsLocalEl.checked : true,
      scripts_dir: "tools/local-nexus",
    };

    const data = await lncFetchJson("/api/import/github-localize-pr", { method: "POST", body: JSON.stringify(payload) });
    if (data && data.repo && data.branch) lncLastPr = { repo: data.repo, branch: data.branch, pr_url: data.pr_url || null };
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

function lncSetMergeDestFromSelected() {
  const el = document.getElementById("mergeDestRepo");
  if (!el) return;
  if (!lncGitHubSelectedRepoFullName) {
    const result = document.getElementById("result");
    if (result) result.textContent = "Select a repo from 'Load my repos' first.";
    return;
  }
  el.value = lncGitHubSelectedRepoFullName;
}

function lncSetMergeSourceFromSelected() {
  const el = document.getElementById("mergeSourceRepo");
  if (!el) return;
  if (!lncGitHubSelectedRepoFullName) {
    const result = document.getElementById("result");
    if (result) result.textContent = "Select a repo from 'Load my repos' first.";
    return;
  }
  el.value = lncGitHubSelectedRepoFullName;
}

async function lncCreateGitHubMergePr() {
  const destRepoEl = document.getElementById("mergeDestRepo");
  const srcRepoEl = document.getElementById("mergeSourceRepo");
  const srcRefEl = document.getElementById("mergeSourceRef");
  const destBaseEl = document.getElementById("mergeDestBase");
  const destSubdirEl = document.getElementById("mergeDestSubdir");
  const result = document.getElementById("result");
  if (!result) return;

  const destRepo = destRepoEl ? String(destRepoEl.value || "").trim() : "";
  const sourceRepo = srcRepoEl ? String(srcRepoEl.value || "").trim() : "";
  const sourceRef = srcRefEl ? String(srcRefEl.value || "").trim() : "";
  const destBase = destBaseEl ? String(destBaseEl.value || "").trim() : "";
  const destSubdir = destSubdirEl ? String(destSubdirEl.value || "").trim() : "";

  if (!destRepo || !sourceRepo) {
    result.textContent = "Enter destination + source repos first (owner/repo).";
    return;
  }

  const token = lncGetGitHubToken();
  if (!token) {
    result.textContent = "Set a GitHub token first (click “GitHub token”).";
    return;
  }

  try {
    const payload = {
      dest_repo: destRepo,
      dest_base: destBase || null,
      dest_subdir: destSubdir || "",
      source_repo: sourceRepo,
      source_ref: sourceRef || "main",
      github_token: token,
      max_files: 250,
      max_total_bytes: 15000000,
    };
    const data = await lncFetchJson("/api/import/github-merge-repos-pr", { method: "POST", body: JSON.stringify(payload) });
    if (data && data.destination && data.branch) lncLastPr = { repo: data.destination, branch: data.branch, pr_url: data.pr_url || null };
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

function lncFillWorkspaceFromLastPr() {
  const repoEl = document.getElementById("wsRepo");
  const branchEl = document.getElementById("wsBranch");
  const result = document.getElementById("result");
  if (!repoEl || !branchEl) return;
  if (!lncLastPr || !lncLastPr.repo || !lncLastPr.branch) {
    if (result) result.textContent = "No recent PR found. Create a merge/localize PR first, then click this.";
    return;
  }
  repoEl.value = lncLastPr.repo;
  branchEl.value = lncLastPr.branch;
  if (result && lncLastPr.pr_url) result.textContent = `Using last PR: ${lncLastPr.pr_url}`;
}

async function lncPrepareWorkspace() {
  const repoEl = document.getElementById("wsRepo");
  const branchEl = document.getElementById("wsBranch");
  const pathEl = document.getElementById("wsPath");
  const result = document.getElementById("result");
  if (!repoEl || !branchEl || !result) return;

  const repo = String(repoEl.value || "").trim();
  const branch = String(branchEl.value || "").trim();
  if (!repo || !branch) {
    result.textContent = "Enter repo + branch first (or click 'Fill from last PR').";
    return;
  }
  const token = lncGetGitHubToken();
  if (!token) {
    result.textContent = "Set a GitHub token first (click “GitHub token”).";
    return;
  }

  try {
    const data = await lncFetchJson("/api/import/github-workspace-prepare", {
      method: "POST",
      body: JSON.stringify({ repo, branch, github_token: token }),
    });
    if (pathEl && data && data.workspace_path) pathEl.value = data.workspace_path;
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

async function lncOpenWorkspaceInCursor() {
  const pathEl = document.getElementById("wsPath");
  const result = document.getElementById("result");
  if (!pathEl || !result) return;
  const workspace_path = String(pathEl.value || "").trim();
  if (!workspace_path) {
    result.textContent = "Prepare workspace first (so the path is filled).";
    return;
  }
  try {
    const data = await lncFetchJson("/api/import/github-workspace-open", {
      method: "POST",
      body: JSON.stringify({ workspace_path }),
    });
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

async function lncPushWorkspaceFixes() {
  const pathEl = document.getElementById("wsPath");
  const branchEl = document.getElementById("wsBranch");
  const msgEl = document.getElementById("wsCommitMessage");
  const result = document.getElementById("result");
  if (!pathEl || !branchEl || !result) return;

  const workspace_path = String(pathEl.value || "").trim();
  const branch = String(branchEl.value || "").trim();
  const commit_message = msgEl ? String(msgEl.value || "").trim() : "";
  if (!workspace_path || !branch) {
    result.textContent = "Workspace path + branch are required (prepare first).";
    return;
  }
  const token = lncGetGitHubToken();
  if (!token) {
    result.textContent = "Set a GitHub token first (click “GitHub token”).";
    return;
  }

  try {
    const payload = { workspace_path, branch, github_token: token, commit_message: commit_message || "Fix after merge/localize in Cursor" };
    const data = await lncFetchJson("/api/import/github-workspace-push", { method: "POST", body: JSON.stringify(payload) });
    result.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    result.textContent = String(e.message || e);
  }
}

async function lncImportFromGitHub() {
  const repoEl = document.getElementById("ghRepo");
  const refEl = document.getElementById("ghRef");
  const pathEl = document.getElementById("ghPath");
  const result = document.getElementById("result");
  if (!repoEl || !result) return;

  const repo = String(repoEl.value || "").trim();
  const ref = refEl ? String(refEl.value || "").trim() : "";
  const path = pathEl ? String(pathEl.value || "").trim() : "";
  if (!repo) {
    result.textContent = "Enter a GitHub repo first (e.g. owner/repo).";
    return;
  }

  try {
    const payload = {
      repo,
      ref: ref || "main",
      path: path || "local-nexus.bundle.json",
      github_token: lncGetGitHubToken() || null,
    };
    const data = await lncFetchJson("/api/import/github-bundle", { method: "POST", body: JSON.stringify(payload) });
    result.textContent = JSON.stringify(data, null, 2);
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
